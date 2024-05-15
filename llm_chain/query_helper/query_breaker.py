from typing import Literal, Optional, Tuple
from langchain.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
import uuid
from typing import Dict, List
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    FunctionMessage
)

from llm_config import USE_LOCAL_LLM, LOCAL_LLM_PORT, OPENAI_MODEL, OPENAI_KEY

def tool_example_to_messages(example: Dict) -> List[BaseMessage]:
    messages: List[BaseMessage] = [HumanMessage(content=example["input"])]
    openai_tool_calls = []
    for tool_call in example["tool_calls"]:
        openai_tool_calls.append(
            {
                "id": str(uuid.uuid4()),
                "type": "function",
                "function": {
                    "name": tool_call.__class__.__name__,
                    "arguments": tool_call.json(),
                },
            }
        )
    messages.append(
        AIMessage(content="", additional_kwargs={"tool_calls": openai_tool_calls})
    )
    tool_outputs = example.get("tool_outputs") or [
        "This is an example of a correct usage of this tool. Make sure to continue using the tool this way."
    ] * len(openai_tool_calls)
    for output, tool_call in zip(tool_outputs, openai_tool_calls):
        messages.append(ToolMessage(content=output, tool_call_id=tool_call["id"]))
    return messages


class SubQuery_with_category(BaseModel):
    """Break down the complex query into self sufficient sub query or queries with appropriate category"""

    sub_query: str = Field(
        ...,
        description="Self-sufficient sub query which can be answered independently",
    )
    category: Literal['hris', 'ats', 'ticketing', 'crm', 'accounting', 'mktg'] = Field(
        ...,
        description="Given a user question choose which datasource would be most relevant for answering their question",
    )
    answer_intro:  str = Field(
        ...,
        description="Intro statement for the answer to the subquery. eg. The list of all employees is present below :")



system = """You are an expert at decomposing complex queries, breaking them down into simple queries and assigning the most relevant category to it.

Perform query decomposition. Given a user question, break it down into distinct sub questions that \
you need to answer in order to answer the original question.

The user will provide you with a complex query which contains multiple queries which need to broken down into simple self-explainable queries. Each simplified query can fall under one of these categories: 

- hris (Human Resource Information Systems)
- ats (Applicant Tracking System))
- crm (Customer Relationship Management)
- ticketing (Ticketing like Jira etc)
- accounting (Accounting )
- mktg (Marketing)
- filestorage (File Storing)

Do not have mentions of one sub-query in another. Each sub-query should be self-sufficient as provided in the examples below.
Do not refer to the past examples. Only decompose the latest user query"""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

base_url = "http://localhost:{port}}/v1"
if USE_LOCAL_LLM:
    # Assuming a functionary model is running on the server using llama cpp
    llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0, base_url=base_url.format(port=LOCAL_LLM_PORT), api_key="functionary")
else:
    llm = ChatOpenAI(model=OPENAI_MODEL,api_key=OPENAI_KEY)

llm_with_tools = llm.bind_tools([SubQuery_with_category])
parser = PydanticToolsParser(tools=[SubQuery_with_category])

examples = []
question = "Get me a list of all employees with inactive employee status, and a list of their open tickets"
queries = [
    SubQuery_with_category(sub_query='Get me a list of all employees in Bangalore.', 
                           category='hris', 
                           answer_intro='The list of all employees in Bangalore is:'),
    SubQuery_with_category(sub_query='What are the open tickets for the above?', 
                           category='ticketing', 
                           answer_intro='The open tickets for all employees in Bangalore is:'),
    ]
examples.append({"input": question, "tool_calls": queries})

example_msgs = [msg for ex in examples for msg in tool_example_to_messages(ex)]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        MessagesPlaceholder("examples", optional=True),
        ("human", "{question}"),
    ]
)
query_decomposer_with_examples = (
    prompt.partial(examples=example_msgs) | llm_with_tools | parser
    )
