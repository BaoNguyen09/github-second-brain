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
    # If it wasn't processed, it will be ingested and return 201
    # Else it will return some error messages

    repo_url_str = str(repo_req.repo_url)
    # Get all processed repo and check if incoming repo was processed
    try:
        res = ingest_repo(repo_url_str)
        if res[0]: # Should return True only on successful *new* processing
            response.status_code = status.HTTP_201_CREATED
            return {"message": f"Repository {repo_url_str} ingested successfully."}
        
        else:
            # Handle different error cases
            if res[1] == "Repository was already processed previously.":
                return {"message": res[1]}
             
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": res[1]}
        
    except Exception as e:
         print(f"ERROR in API processing {repo_url_str}: {e}") # Log the error
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
         return {"message": f"Failed to process repository {repo_url_str} due to an internal error."}
    
    