import chromadb
from chromadb.config import Settings
import ast 


from commons.constants import EMBEDDINGS_COLLECTION_NAME, CHROMADB_PORT

class EmbeddingHelper:
    @staticmethod
    def get_relevant_merge_apis(sub_query, category, num_results=5):
        client = chromadb.HttpClient(host='localhost', port=CHROMADB_PORT, settings=Settings(anonymized_telemetry=False))
        collection = client.get_collection(EMBEDDINGS_COLLECTION_NAME)
        
        res = collection.query(query_texts=[sub_query], 
                           n_results=num_results, 
                           where={"category": category})

        # most relevant merge apis to answer the query in form of openai tools
        
        # The endpoints have already been converted to dictionary which is in openai compatible format
        # The complete dictionary has been saved in chroma as is, to easily get back the function using vector search
        
        
        # A more proper implementation would be to use django + mysql to store tool definitions + vector id
        # , and store the vector ids in milvus/chroma/etc
        
        tools = [ast.literal_eval(x)['function'] for x in res['documents'][0]]
        
        return tools
        
        