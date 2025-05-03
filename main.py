from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from process_repo import ingest_repo

class RepoRequest(BaseModel):
    repo_url: HttpUrl

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/v1/process")
async def process_repo(repo_req: RepoRequest):
    # write a function to pass this repo_req to gitingest
    repo_req_dict = repo_req.model_dump()
    # will later have a function to check if repo is processed
    # and stored in database before ingesting it
    await ingest_repo(str(repo_req.repo_url))
    pass