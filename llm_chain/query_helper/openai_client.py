from openai import OpenAI
from ..llm_config import USE_LOCAL_LLM, LOCAL_LLM_PORT, OPENAI_KEY, OPENAI_MODEL

if USE_LOCAL_LLM:
    # assuming local llm has this type of endpoint
    local_llm_endpoint = "http://localhost:{llm_port}}/v1"
    local_llm_endpoint = local_llm_endpoint.format(llm_port=LOCAL_LLM_PORT)
    client = OpenAI(base_url=local_llm_endpoint, api_key="functionary")
    model = ""
else:
    client = OpenAI(api_key=OPENAI_KEY)
    model = OPENAI_MODEL

class OpenAIClient:
    def get_response(self, messages):
        """Helps to generate responses from given messages/prompt"""
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            top_p=1e-7
        )
        
        return response
    
    def get_endpoints_and_params_from_openai(self, messages, tools):
        """Get details of relevant Merge Endpoint with required params"""
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="required",
            temperature=0.1,
            top_p=1e-7
        )
        
        return response
    