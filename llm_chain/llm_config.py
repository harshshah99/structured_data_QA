import os

def get_bool(var, default=False):
    var = os.getenv(var)
    if var and var.lower() == "false":
        return False
    elif var and var.lower() == "true":
        return True
    else:
        return default


USE_LOCAL_LLM = get_bool('USE_LOCAL_LLM')
OPENAI_KEY = os.getenv('OPENAI_KEY','OPENAI_KEY_HERE')
OPENAI_MODEL = os.getenv('OPENAI_MODEL','gpt-4o')

LANGSERVE_PORT = int(os.getenv('LANGSERVE_PORT','1111'))
LOCAL_LLM_PORT = int(os.getenv('LOCAL_LLM_PORT','8000'))