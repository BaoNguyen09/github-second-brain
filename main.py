from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from process_repo import ingest_repo

class RepoRequest(BaseModel):
    repo_url: HttpUrl

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/v1/process")
async def process_repo(repo_req: RepoRequest, background_tasks: BackgroundTasks):
    # will later have a function to check if repo is processed
    # and stored in database before ingesting it
    background_tasks.add_task(ingest_repo, str(repo_req.repo_url))
    return {"message": "Repo is being ingested in the background"} 