from fastapi import FastAPI, Response, status, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from process_repo import ingest_repo, get_directory_structure, is_processed_repo

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
            return {
                "message": f"Repository {repo_url_str} ingested successfully.", 
                "output_path": res[2]
                }
        
        else:
            if res[1] == "Repository was processed previously.":
                return {
                    "message": res[1],
                    "output_path": res[2]
                    }
            
            # Handle different error cases
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": res[1]}
        
    except Exception as e:
         print(f"ERROR in API processing {repo_url_str}: {e}") # Log the error
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
         return {"message": f"Failed to process repository {repo_url_str} due to an internal error."}
    
@app.get("/api/v1/dir-tree", status_code=200)
def get_dir_tree(repo_req: RepoRequest, response: Response, background_tasks: BackgroundTasks):
    repo_url_str = str(repo_req.repo_url)

    # check if incoming repo was processed
    try:
        processing_status = is_processed_repo(repo_url_str, True)
        if processing_status:
            return {
                "message": "Success",
                "directory_tree": get_directory_structure(repo_url_str)
            }

        # Else, return a response and process the repo in background
        background_tasks.add_task(process_repo, repo_req, response)
        response.status_code = status.HTTP_202_ACCEPTED
        return {
            "message": f"Repository {repo_url_str} is being processed now, come back later.",
        }
        
    except Exception as e:
         print(f"ERROR in API tree fetching for repo '{repo_url_str}': {e}") # Log the error
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
         return {"message": f"Failed to fetch directory tree of {repo_url_str} due to an internal error."}