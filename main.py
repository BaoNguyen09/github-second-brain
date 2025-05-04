from fastapi import FastAPI, Response, status
from pydantic import BaseModel, HttpUrl
from process_repo import ingest_repo

class RepoRequest(BaseModel):
    repo_url: HttpUrl

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/v1/process", status_code=200)
async def process_repo(repo_req: RepoRequest, response: Response):
    # This method will return 200 if the repo is already processed
    # Else it will process and return 201

    # Get all processed repo and check if incoming repo was processed
    if ingest_repo(str(repo_req.repo_url)):
        response.status_code = status.HTTP_201_CREATED
        return {"message": "Repo has been ingested successfully"}
    
    return {"message": "This repo was processed"}