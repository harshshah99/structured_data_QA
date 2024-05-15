import json
import logging
import sys
from openai import OpenAI


from commons.constants import API_CACHE_PATH, API_CATEGORIES

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class OpenAiToolsHelper:
    def __init__(self) -> None:
        self.tools = []
        self.categories = [] #to be used as metadata in vector db
        self.endpoint_and_resp_format = {}

    def get_all_tools_and_categories(self):
        """Iterate through the schema of every API category in merge and convert all these specs to OpenAI tool format.
        Returns the tools, categories and endpoint, response format mapped to the tool name
        """
        LOGGER.info(f"Converting all Merge category OpenAPI spec to OpenAI function call format")
        for category in API_CATEGORIES:
            print("Converting tools for : ", category)
            with open(API_CACHE_PATH + category + '.json','r') as f:
                openapi_spec = json.load(f)

            tools, endpoint_and_resp_format = OpenAiToolsHelper.openapi_to_tools(openapi_spec, category)
            self.tools.extend(tools)
            self.categories.extend([category]*len(tools))
            self.endpoint_and_resp_format.update(endpoint_and_resp_format)

        return self.tools, self.categories, self.endpoint_and_resp_format

    @staticmethod
    def openapi_to_tools(openapi_spec, category):
        """
        Takes in openapi schema/spec for an API. And converts it into OpenAI tool call format compatible function. 
        This parser has been modified to work with merge.dev api schemas in particular.
        Minor changes may be needed to make it compatible to ANY Openapi schema 
        """
        functions = []
        endpoint_and_resp_format = {}
        for path, methods in openapi_spec["paths"].items():
            for method, spec in methods.items():
                # Since we are only dealing with finding information, we will ignore methods other than get
                if method!='get':
                    continue

                function_name = spec.get("operationId")

                desc = spec.get("description") or spec.get("summary", "")

                schema = {"type": "object"}

                params = spec.get("parameters", [])
                response = (spec.get("responses", {})
                    .get("200",{})
                    .get("content", {})
                    .get("application/json", {})
                    .get("schema"))

                if params:
                    required_params = []
                    param_properties = {}
                    for param in params:
                        name = param['name']
                        basic_schema = {'type' : param['schema']['type']}
                        formating_details = basic_schema.get('format',"")
                        if formating_details:
                            formating_details = ". The format should be " + formating_details 
                        enum = basic_schema.get('enum',None)

                        if enum:
                            basic_schema.update({'enum':enum})

                        description = param.get('description','') + formating_details
                        basic_schema.update({'description': description})

                        if param.get('required',None):
                            required_params.append(name)

                        param_properties.update({name:basic_schema})

                schema.update({'properties':param_properties, 'required':required_params})

                # also return the response format to provide additional context to the model
                functions.append(
                    {
                        "function": {
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "description": desc,
                                "parameters": schema,
                            }
                        }
                        
                    }
                )

                endpoint_and_resp_format.update({function_name: {'endpoint': category + '/v1' + path,
                                                                'response_format' : response }})

        return functions, endpoint_and_resp_format
