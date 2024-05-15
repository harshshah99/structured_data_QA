## Repo Structure:

```
├── README.md - 
├── api_cache - Contains the Cached OpenAPI schemas for each major API category in merge 
│   ├── accounting.json
│   ├── ats.json
│   ├── crm.json
│   ├── hris.json
│   ├── mktg.json
│   ├── schema_cache.json
│   └── ticketing.json
├── commons - Constants used throughout the app like category names, descriptions, ports to expose, Merge keys and more
│   └── constants.py
├── complete_conversation_final_prompt.json - Generated after running main.py, contains the complete OpenAI message list for the sequential chain
├── endpoint_and_resp_format.json - Contains mapping of OperationId as present in OpenAPI schema with endpoint path  and response format for that particular endpoint
├── example_notebook.ipynb - Example notebook with relevant headers. Almost same code as main.py, but more clean
├── example_notebook_final_prompt.json
├── helper_funcs - Helper functions for common API tasks , Chroma (Vector DB) tasks and OpenAI tool conversions
│   ├── api_helper.py
│   ├── embedding_helper.py
│   └── openai_helper.py
├── llm_chain - Langchain project for LLM related endpoints. Deploys a fastapi langserve server which we can use for LLM/Chain related tasks
│   ├── README.md
│   ├── app
│   ├── llm_constants.py
│   ├── packages
│   ├── pyproject.toml
│   ├── query_helper
│   └── trial
├── main.py - The main script to run QA on structured data (Assuming data can be fetched from one of the MERGE APIs)
├── requirements.txt
├── update_all_data.py - Updates all the schemas in api_cache/, embeddings in vector_db/ (takes around 5-10 mins to run but is not needed to run everytime since API schemas don't change so often)
└── vector_db - Contains Chroma vector embeddings
```
## Application Diagram

Design Diagram for this application - [application_diagram](application_diagram.pdf) 


## Environment Variables

Environment Variables are present in:
- [.env](.env) - Contains only Chroma PORT currently
- [llm_chain/.env](llm_chain/.env) - Contains LLM specific environment variables. OpenAI platform key and model need to be added here

#### Note. The exporting variables from .env part in the bash scripts may not work perfectly. In that case, the important variables you would need to add directly in the python file are:
- [Merge API keys](commons/constants.py#L26-27)
- [OpenAI API key](./llm_chain/llm_config.py#L14)

## Required bash scripts to setup the environment and start relevant servers:

Make these scripts executable:
```
chmod +x ./setup-conda-env ./start-langserve ./start-chroma
```

1. Run `./setup-conda-env` first to setup a conda environment named project. If you plan to change this conda environment name, you will need to change Line 7 in [./start-chroma](./start-chroma#L7) and [./start-langserve](./start-langserve#L7)
2. Open two terminals. Run `source start-chroma` in one and `source start-langserve` in the other. Keep this two running

### If using a virtual env instead of conda or setting up conda without using `./setup-conda-env` script, activate the virtual/conda environment and install the packages in the following way:
```
pip install -r requirements.txt
pip install langchain-cli
```

Doing a pip freeze or conda env export was causing dependency issues and a failed pip/conda install. Because of this, two seperate pip commonds need to be run.

## Updating the local data
Create following directories if they are not present
```
mkdir vector_db
mkdir api_cache
```

The following command:
```
python update_all_data.py
```
1. Downloads all the schemas locally
2. Converts them to openai tool/function format
3. Saves a map of openai tool/function name -> Merge Endpoint, Response Format for that particular method
4. Saves the tool dicts , its embeddings and metadata (API category : hris, ats, etc) in chroma

This takes around 10 mins to run (because of chroma primarily). But since API schema does not change that often, it can be run periodically

## Running the main file
Ensure that Chroma and Langserve servers are running

The [main](main.py) file combines the complete flow, taking in a complex query and outputting the final answer. 

```
conda activate project
export TOKENIZERS_PARALLELISM=false #without this unnecessary logs would show up
python main.py --question "For all employees in Bangalore, how many rounds of interview have they had and how many of their critical tickets are open"
```

The complete user message for the previous question asked in the below format will be present in [complete_conversation_final_prompt.json](complete_conversation_final_prompt.json):
```python
[
    {User : Sub-Query1},
    {Assistant : Data for Sub-Query1 from Merge},
    {User : Sub-Query2},
    {Assistant : Data for Sub-Query2 from Merge},
    {User : Complete Question}
]
```

## Example Notebook
There is also an [example notebook](example_notebook.ipynb) present, containing almost exactly same code as [main.py](main.py). It has relevant headers explaining what each code block is doing with populated examples in the cell outputs.


## Possible Improvements

- Having a dedicated DB with models (Django+MySQL) connected to a Vector DB instead of current implementation (storing all strings and embeddings in one place) would be much more performant
- The prompts in [main.py](main.py) can be handled better
- Having the OpenAI Client as an LLM endpoint inside langserve would package all LLM related functionality in one place
- Currently, LOGGER is used to print directly into the console to see the flow
- Using a better quality embedding model. With chroma, custom sentence transformer models were erroring out. The current embeddings are from `all-MiniLM-L6-v2`. Using a model trained on code would yield better embeddings and thus more accurate tool calls
