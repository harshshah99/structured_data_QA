import requests
import jsonref
import json
import hashlib
import sys
import logging

from commons.constants import API_CATEGORIES, API_CACHE_PATH, API_BASE_URL, URL_FORMAT, MERGE_API_TOKEN, END_USER_ACCOUNT_TOKEN

LOGGER = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class ApiHelper:

    @staticmethod
    def populate_api_cache():
        """Iterate through schemas for all API Categories and save their openapi schema locally"""
        schema_hash = {}
        for category in API_CATEGORIES:
            LOGGER.info(f"Getting schema for category : {category}")
            final_url = URL_FORMAT.format(base_url=API_BASE_URL, api_category=category)
            schema = requests.get(final_url).text
            schema = jsonref.loads(schema)
            resolved_schema = jsonref.replace_refs(schema)
                        
            with open(API_CACHE_PATH + category + '.json', 'w') as f:
                jsonref.dump(resolved_schema, f)
                
            schema_hash.update({category:hashlib.md5(str(resolved_schema).encode()).hexdigest()})
        
        with open(API_CACHE_PATH + 'schema_cache.json','w') as f:
            json.dump(schema_hash,f)
            
    @staticmethod
    def get_response_from_merge(endpoint, params):
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {api_key}'.format(api_key=MERGE_API_TOKEN),
            'X-Account-Token': END_USER_ACCOUNT_TOKEN
            }
                
        base_url = API_BASE_URL
        # Extract path variables
        path_variables = {key: params[key] for key in params if '{' + key + '}' in endpoint}

        excluded_keys = set(path_variables.keys()).union(headers.keys())

        # Remove path variables from the params dictionary to avoid duplication in the query string
        query_params = {key: params[key] for key in params if key not in excluded_keys}

        # Format the endpoint with the path variables
        endpoint = endpoint.format(**path_variables)

        url = f"{base_url}/{endpoint}"
        
        LOGGER.info(f"\n----------- MERGE ENPOINT AND PARAM DETAILS -------------\n")
        LOGGER.info(f"Calling Merge endpoint : {url} ")
        LOGGER.info(f"With Params : {query_params} \n")
        LOGGER.info(f"\n---------------------------------------------------------\n")

        response = requests.get(url=url, headers=headers, params=query_params)
        
        return response.text
        