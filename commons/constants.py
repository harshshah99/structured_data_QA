"""
Contains all common variables used throughout the project
"""
import os

script_path = os.path.join(os.path.dirname(__file__))

API_CATEGORIES = {
    "hris": "The unified API for building rich integrations with multiple HR Information System platforms.",
    "ats": "The unified API for building rich integrations with multiple Applicant Tracking System platforms.",
    "ticketing": "The unified API for building rich integrations with multiple Ticketing platforms.",
    "crm": "The unified API for building rich integrations with multiple CRM platforms.",
    "accounting": "The unified API for building rich integrations with multiple Accounting & Finance platforms.",
    "mktg": "The unified API for building rich integrations with multiple Marketing Automation platforms.",
}

EMBEDDINGS_COLLECTION_NAME = 'merge_api_endpoints'

API_BASE_URL = "https://api.merge.dev/api"
URL_FORMAT = "{base_url}/{api_category}/v1/schema"

API_CACHE_PATH = os.path.join(script_path, '..', "api_cache/")
VECTOR_DB_PATH = os.path.join(script_path, '..', "vector_db/")

CHROMADB_PORT = int(os.getenv('CHROMADB_PORT','9090'))
MERGE_API_TOKEN =  os.getenv('MERGE_API_TOKEN','YOUR_MERGE_API_TOKEN')
END_USER_ACCOUNT_TOKEN = os.getenv('END_USER_ACCOUNT_TOKEN','END_USER_TOKEN')