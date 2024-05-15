from langserve import RemoteRunnable
import json
import logging
import sys
import argparse

from commons.constants import API_BASE_URL
from llm_chain.query_helper.openai_client import OpenAIClient, model
from llm_chain.llm_config import LANGSERVE_PORT
from helper_funcs.openai_helper import OpenAiToolsHelper
from helper_funcs.embedding_helper import EmbeddingHelper
from helper_funcs.api_helper import ApiHelper

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
# To avoid httpx logs from coming up
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("-q", "--question", type=str)
args = parser.parse_args()
if args.question is None:
    parser.error("-q / --question paramater is required")


question_and_responses_template = """Answer : {intro_text}

Response from endpoint : {endpoint}
{api_response}

_______________________
The above data follows this response format : 
{resp_format}

____________________________

"""
final_user_message = """
Given all the details discussed previosuly in this conversation, answer this questions:

Question : {complex_user_query}"""

open_ai = OpenAIClient()

# this json contains a hmap of every OperationID to (endpoint , response_format)
# The tool name passed to openai is this OperationID as it is unique for every endpoint in a OpenAPI schema
# This map will be used to
# a) get back endpoint which we can use to create a GET request and get data
# b) provide context of what the response format is so that LLM can construct the final answer better
with open("endpoint_and_resp_format.json", "r") as f:
    endpoint_and_resp_format_data = json.load(f)

# The complex user query which is to be answered
complex_user_query = args.question

LOGGER.info(f"Complex User Query : {complex_user_query}")
query_decomposer_input = {"question": complex_user_query}

LANGSERVE_ENPOINT = "http://127.0.0.1:{port}"
LANGSERVE_ENPOINT = LANGSERVE_ENPOINT.format(port=LANGSERVE_PORT)

query_decompose = RemoteRunnable(LANGSERVE_ENPOINT + "/query_breaker")

# Get sub-queries for the complex user query
sub_queries = query_decompose.invoke(query_decomposer_input)

# This will keep track of each sub-query and the data returned from merge apis
# Each sub-query will be present as user message, followed by the data returned from merge in assistant message
# At the end of all sub-queries and responses, the original complex question will be appended to this
# and the complete list will be sent to openai for constructing the final answer
oai_messages=[]


# Iterate over the list of sub-queries sequentially
for sub_query in sub_queries:
    sub_q = sub_query["sub_query"]
    category = sub_query["category"]
    intro = sub_query["answer_intro"]

    LOGGER.info(
        f"\nGetting relevant endpoint and params for Question : {sub_q} ,Category : {category}........\n"
    )

    # get 10 most relevant endpoints to the current sub-query in openai tools format
    # use category to filter out results from unwanted categories
    tools = EmbeddingHelper.get_relevant_merge_apis(sub_q, category, num_results=10)
    oai_messages.append({'role':'user','content':sub_q})

    # send the current sub-query to openai with above filtered tools
    # get back details of which tool(endpoint) to call with what arguments(query params)
    endpoint_with_params = open_ai.get_endpoints_and_params_from_openai(
        oai_messages, tools
    )

    func_name = endpoint_with_params.choices[0].message.tool_calls[0].function.name
    arguments = json.loads(
        endpoint_with_params.choices[0].message.tool_calls[0].function.arguments
    )

    endpoint = endpoint_and_resp_format_data[func_name]["endpoint"]
    response_format = endpoint_and_resp_format_data[func_name]["response_format"]

    # Get data by making a GET request to relevant merge endpoint with required arguments
    curr_response = ApiHelper.get_response_from_merge(endpoint, arguments)

    curr_assistant_message = question_and_responses_template.format(
        subquestion=sub_q,
        intro_text=intro,
        endpoint=endpoint,
        api_response=curr_response,
        resp_format=response_format,
    )
    
    oai_messages.append({'role':'assistant','content':curr_assistant_message})

oai_messages.append({'role':'user', 'content' : final_user_message.format(complex_user_query=complex_user_query)})


# The final llm call to get back the answer to the complete user question,
# uncomment this after adding Merge api keys in .env/ constants.py
oai_final_res = open_ai.get_response(oai_messages)
LOGGER.info(f"The answer is  : {oai_final_res.choices[0].message.content}")

# Dump the complete message in a file so that we can see what the conversation sent to LLM looks like
with open('complete_conversation_final_prompt.json','w') as f:
    json.dump(oai_messages,f)