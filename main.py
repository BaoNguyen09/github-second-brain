from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

class RepoRequest(BaseModel):
    repo_url: HttpUrl

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/api/v1/process")
async def process_repo(repo_req: RepoRequest):
    # write a function to pass this repo_req to gitingest
    pass