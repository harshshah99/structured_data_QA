from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from langserve import add_routes

from query_helper.query_breaker import query_decomposer_with_examples

app = FastAPI()


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


# Edit this to add the chain you want to add
add_routes(app, query_decomposer_with_examples, path = '/query_breaker')

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
