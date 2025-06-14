import os, sys, traceback
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from fastmcp.prompts.prompt import Message
import httpx
from pydantic import BaseModel, HttpUrl
from tools.fetch_file_contents import fetch_file_contents
from tools.fetch_issue_context import fetch_issue_context
from tools.fetch_directory_tree import fetch_directory_tree_with_depth
from tools.fetch_diffs import fetch_diffs
from tools.custom_errors import GitHubApiError
from prompt import base_prompt

# Initialize FastMCP server
mcp = FastMCP("Github-Second-Brain")
github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")

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

@mcp.tool()
async def get_directory_tree(
    owner: str,
    repo: str,
    ref: str = "",
    depth: int = 1,
    full_depth: bool = False,
) -> str:
    """
    Get directory tree of repository with specified depth

    Args:
        owner: The owner of the GitHub repository
        repo: The name of the GitHub repository
        ref: Branch name, tag, or commit SHA of specified tree
        depth: The specified depth of the tree in int
        full_depth: The bool determine whether to get tree w/ full_depth

    Return:
        str: the directory tree with specified depth as a string
    """
    # Add a check for owner + repo fields, they're required
    if not repo or not owner:
        return "repo and owner fields are required"
    
    try:
        if ref == "":
            ref = None
        async with httpx.AsyncClient() as client: # dependency for httpx async client
            return await fetch_directory_tree_with_depth(owner, repo, client, ref, github_token, depth, full_depth)
    
    except Exception as e:
        error = f"ERROR in API tree fetching for /{owner}/{repo}/{ref} with depth {depth}: {e}"
        print(error) # Log the error
        return error
    

@mcp.tool()
async def get_repo_contents(
    owner: str,
    repo: str,
    path: str = "",
    ref: str = "",
) -> str:
    """
    Get a file or directory from the repo

    Args:
        owner: Repository owner (username/organization)
        repo: Repository name
        path: Path to file/directory
        ref: The name of the commit/branch/tag. Default: the repository’s default branch

    Return:
        str: the content of the file or directory requested
    """
    if not repo or not owner:
        return "repo and owner fields are required"
    
    try:
        async with httpx.AsyncClient() as client: # dependency for httpx async client
            contents = await fetch_file_contents(owner, repo, path, client, ref, github_token)
        return contents[0]

    except Exception as e:
        error = f"ERROR in API content fetching for {owner}/{repo}?ref={ref}&path={path}: {e}"
        print(error) # Log the error
        return error

@mcp.tool()
async def get_issue_context(
    owner: str,
    repo: str,
    issue_number: str
) -> Dict[str, Any]:
    """Get issue context from any public github repository.

    Args:
        repo_url: a valid GitHub repository link
        issue_number: a string number of the wanted issue

    Return:
        Dict: A dictionary containing the structured issue context.
    """
    if not repo or not owner:
        return "repo and owner fields are required"
    
    try:

        if not issue_number.isnumeric or int(issue_number) <= 0:
            raise ValueError("Issue number must be a positive integer.")
        async with httpx.AsyncClient() as client: # dependency for httpx async client
            raw_context_data = await fetch_issue_context(owner, repo, int(issue_number), client, github_token)
        # Basic check to ensure essential data is there before Pydantic validation
        if not all(k in raw_context_data for k in ["number", "title", "state", "html_url", "user", "created_at", "comments"]):
            raise Exception(detail="Internal data processing failed: missing essential fields from GitHub client.")

        return GitHubIssueContextResponse(**raw_context_data)
    
    except ValueError:
        error_msg = "Invalid issue number. It must be a string representing a positive integer."
        print(error_msg)
        return {
            "error": True,
            "message": error_msg,
            "input_issue_number": issue_number
        }
    
    except Exception as e:
        error_log_message = (
            f"MCP tool 'get_issue_context' failed for {owner}/{repo}#{issue_number}. "
            f"Error calling internal tool: {type(e).__name__} - {str(e)}."
        )
        print(error_log_message) # Server-side log

        # Generic error message for the AI
        return {
            "error": True,
            "message": (
                f"Could not retrieve context for issue '{issue_number}' in repository '{owner}/{repo}'. "
                "Please ensure the repository URL and issue number are correct. "
                "If the problem persists, the backend service might be experiencing issues."
            )
        }

@mcp.tool()
async def get_code_diff(
    owner: str,
    repo: str,
    pr_number: int = 0,
    base_ref: str = "",
    head_ref: str = ""
) -> Dict[str, Any]:
    """
    Gets the diff content directly from the GitHub API.

    This function operates in two modes:
    1. PR Mode: If `pr_number` is provided, it fetches the diff for that Pull Request.
    2. Compare Mode: If `base_ref` and `head_ref` are provided, it fetches the diff
       between these two commits/branches/tags.

    Args:
        owner: The owner of the GitHub repository
        repo: The name of the GitHub repository
        http_client: An instance of httpx.AsyncClient for making requests
        github_token: Optional GitHub API token for authentication
        pr_number: A pull request id number
        base_ref: Branch name, tag, or commit SHA
        head_ref: Branch name, tag, or commit SHA

    Returns:
        A dictionary containing the diff content or an error message.
    """
    if not repo or not owner:
        return {"error": True, "message": "Invalid arguments: repo and owner fields are required"}
    
    if not pr_number and not (base_ref and head_ref):
        return {"error": True, "message": "Invalid arguments: You must provide either 'pr_number' or both 'base_ref' and 'head_ref'."}
    
    if pr_number < 0:
        return {"error": True, "message": "Invalid arguments: 'pr_number' must be a non-negative integer"}

    try:
        async with httpx.AsyncClient() as client:
            results = await fetch_diffs(
                owner=owner,
                repo=repo,
                http_client=client,
                github_token=github_token,
                pr_number=pr_number,
                base_ref=base_ref,
                head_ref=head_ref
            )
        return results
    
    except GitHubApiError as e:
        print(f"GitHubApiError in diff tool: {e}", file=sys.stderr)
        return {"error": True, "message": f"Failed to fetch diff from GitHub API: {str(e)}", "details": e.details}
    except Exception as e:
        print(f"Unexpected error in get_code_diff tool: {type(e).__name__} - {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"error": True, "message": "An unexpected server-side error occurred while processing the diff."}

@mcp.prompt()
def analyze_github_repository(
    focus: str = "Let me explore and decide what's most important for each user's request"
) -> Message:
    """Comprehensive guide for analyzing GitHub repositories using all available tools."""

    return Message(f"{base_prompt}\n**Focus area:** {focus}")

if __name__ == "__main__":
    print("MCP Server script starting...", file=sys.stderr)

    # Check for the optional environment variable
    if not github_token or github_token == "":
        print("WARNING: github token environment variable not set!", file=sys.stderr)

    try:
        print("Attempting to start mcp.run(transport='stdio')...", file=sys.stderr)
        mcp.run(
            transport='stdio',
        )
        print("mcp.run() finished.", file=sys.stderr) # Should not be reached if it's a long-running server
    except ImportError as e:
        print(f"MCP Server exiting due to ImportError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"MCP Server exiting due to an unhandled exception: {type(e).__name__} - {e}", file=sys.stderr)
        # Print traceback for more details
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        print("MCP Server script attempting to exit.", file=sys.stderr)