import chromadb
import logging
import sys
import json

from helper_funcs.openai_helper import OpenAiToolsHelper
from helper_funcs.api_helper import ApiHelper
from commons.constants import VECTOR_DB_PATH, EMBEDDINGS_COLLECTION_NAME

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


LOGGER.info(f"Create a local copy of Merge API schema....")
_ = ApiHelper.populate_api_cache()

LOGGER.info(f"Converting OpenAPI schema to OpenAI tools format....")
openai_helper = OpenAiToolsHelper()

tools, categories, endpoint_and_resp_format_info= openai_helper.get_all_tools_and_categories()

# save a map of function name used (operationId) and {endpoint, response format}
# these will help while implementing the complete QA pipeline
with open('endpoint_and_resp_format.json', 'w') as f:
    json.dump(endpoint_and_resp_format_info, f)


client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
existing_collections = [c.name for c in client.list_collections()]

if EMBEDDINGS_COLLECTION_NAME in existing_collections:
    LOGGER.info(f"Collection : {EMBEDDINGS_COLLECTION_NAME} already exists. Deleting it")
    client.delete_collection(EMBEDDINGS_COLLECTION_NAME)

collection = client.create_collection(name=EMBEDDINGS_COLLECTION_NAME)


# The complete tool dict is converted to str and saved in chroma
# so when it is retrieved by vector search, we can get back the original tools with ast.literal_eval
LOGGER.info(f"Adding tool definitions and embeddings to Chroma Collection : {EMBEDDINGS_COLLECTION_NAME}")
collection.add(
    documents=[str(tool) for tool in tools],
    ids=[str(i+1) for i in range(len(tools))],
    metadatas=[{'category':c} for c in categories]
)