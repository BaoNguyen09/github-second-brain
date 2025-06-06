from fastapi import Depends, FastAPI, HTTPException, Path, Response, status, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from app.internal_tools.github_api_client import fetch_issue_context, GitHubApiError, fetch_directory_tree_with_depth, fetch_file_contents
from app.internal_tools.process_repo import ingest_repo, get_directory_structure, is_processed_repo, get_a_file_content
from typing import List, Optional
import httpx

class RepoRequest(BaseModel):
    repo_url: HttpUrl
    file_path: Optional[str] = None

class GitHubIssueCreator(BaseModel):
    login: str
    html_url: Optional[HttpUrl] = None # html_url can sometimes be missing for system users

class IssueCommentDetail(BaseModel):
    user: GitHubIssueCreator
    created_at: Optional[str] = None # Or datetime
    body: str
    html_url: Optional[HttpUrl] = None

class GitHubIssueContextResponse(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    state: str
    html_url: HttpUrl
    user: GitHubIssueCreator
    created_at: str # Or datetime
    comments_count: int
    comments: List[IssueCommentDetail]

app = FastAPI()

# --- Dependency for HTTP client ---
async def get_http_client():
    async with httpx.AsyncClient() as client:
        yield client

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

@app.get("/api/v1/directory-tree/{owner}/{repo}", status_code=200)
async def get_tree(
    response: Response,
    owner: str = Path(..., description="The owner of the GitHub repository."),
    repo: str = Path(..., description="The name of the GitHub repository."),
    ref: str = None,
    depth: int = 1,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    try:
        if ref == "":
            ref = None
        tree = await fetch_directory_tree_with_depth(owner, repo, client, ref, GITHUB_TOKEN, depth)
        if "Directory structure:" in tree:
            return {"message": "Success", "directory tree": tree}
        
        return {"message": tree}
    
    except Exception as e:
        error = f"ERROR in API tree fetching for /{owner}/{repo}/{ref} with depth {depth}: {e}"
        print(error) # Log the error
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"message": error}
    
@app.get("/api/v1/contents/{owner}/{repo}", status_code=200)
async def get_contents(
    response: Response,
    owner: str = Path(..., description="The owner of the GitHub repository."),
    repo: str = Path(..., description="The name of the GitHub repository."),
    path: str = "",
    ref: str = None,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    if ref == "":
        ref = None
    contents = await fetch_file_contents(owner, repo, path, client, ref, GITHUB_TOKEN)
    if contents is not None:
        return {"message": "Success", "contents": contents}
    
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"message": contents[1]}

@app.get("/api/v1/issue-context/{owner}/{repo}/{issue_number}",
           response_model=GitHubIssueContextResponse,
           summary="Get context for a specific GitHub issue including title, body, and comments.",
)
async def get_github_issue_context_api(
    owner: str = Path(..., description="The owner of the GitHub repository."),
    repo: str = Path(..., description="The name of the GitHub repository."),
    issue_number: int = Path(..., description="The issue id number."),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """
    Fetches the title, body, state, and all comments for a given GitHub issue
    by calling the github_api_client.
    """
    try:
        raw_context_data = await fetch_issue_context(
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            http_client=client,
        )

        # Basic check to ensure essential data is there before Pydantic validation
        if not all(k in raw_context_data for k in ["number", "title", "state", "html_url", "user", "created_at", "comments"]):
            raise HTTPException(status_code=500, detail="Internal data processing failed: missing essential fields from GitHub client.")

        return GitHubIssueContextResponse(**raw_context_data)

    except GitHubApiError as e:
        # Handle custom errors from your API client
        raise HTTPException(status_code=e.status_code or 500, detail=str(e))
    except HTTPException: # Re-raise FastAPI's own HTTPExceptions
        raise
    except Exception as e:
        # Catch-all for other unexpected errors during the API endpoint handling
        print(f"Unexpected error in API endpoint /api/v1/issue-context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected internal server error occurred: {str(e)}")