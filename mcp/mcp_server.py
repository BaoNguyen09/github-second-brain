import os, sys, traceback
import re
from typing import Any, Dict
from fastmcp import FastMCP
import requests

# Initialize FastMCP server
mcp = FastMCP("Github-Second-Brain")
root_url = os.getenv("GHSB_API_ENDPOINT", "http://127.0.0.2:8080")
@mcp.tool()
def get_processed_repo(repo_url: str) -> str:
    """Get repository that was processed and stored.
    TODO: i need a way to handle unprocessed repo, 
          otherwise it the tool call will time out

    Args:
        repo_url: a valid GitHub repository link

    Return:
        str: the full content of file containing processed data
    """

    payload = {
        "repo_url": repo_url
    }
    url = f"{root_url}/api/v1/process"
    response = requests.post(url, json=payload, timeout=30)
    data = response.json()
    # wait for response, and get the filename
    if "output_path" in data:
        output_path = data["output_path"]
        # then search in data folder for that file and return the content
        with open(output_path, "r", encoding='utf-8') as file:
            content = file.read()

        return content if content else "Couldn't read the file"
    
    return data["message"]

@mcp.tool()
async def get_directory_tree(
    owner: str,
    repo: str,
    ref: str = None,
    depth: int = 1
) -> str:
    """
    Get directory tree of repository with specified depth

    Args:
        owner: The owner of the GitHub repository
        repo: The name of the GitHub repository
        ref: Branch name, tag, or commit SHA of specified tree
        depth: The specified depth of the tree in int

    Return:
        str: the directory tree with specified depth as a string
    """
    # Add a check for owner + repo fields, they're required
    if not repo or not owner:
        return "repo and owner fields are required"
    
    url = f"{root_url}/api/v1/directory-tree/{owner}/{repo}?ref={ref}&depth={depth}"
    response = requests.get(url, timeout=30)
    data = response.json()

    # wait for response, and get the file content
    if data["message"] == "Success":
        return data["directory tree"]
    
    return data["message"]


@mcp.tool()
def get_file_content(repo_url: str, file_path: str = "directory_tree") -> str:
    """Get content of a file from a processed repository.

    Args:
        repo_url: a valid GitHub repository link
        file_path: a valid, existing path to a file (no leading or trailing "/")
                    (By default, it will return the tree directory)
    Return:
        str: the full content of that file in plain text
    """

    payload = {
        "repo_url": repo_url,
        "file_path": file_path
    }
    url = f"{root_url}/api/v1/get-file"
    response = requests.get(url, json=payload, timeout=30)
    data = response.json()

    # wait for response, and get the file content
    if data["message"] == "Success":
        return data["content"]
    
    return data["message"]

@mcp.tool()
def get_issue_context(repo_url: str, issue_number: str) -> Dict[str, Any]:
    """Get issue context from any public github repository.

    Args:
        repo_url: a valid GitHub repository link
        issue_number: a string number of the wanted issue

    Return:
        Dict: A dictionary containing the structured issue context.
    """
    owner = ""
    repo_name = ""

    # 1. Parse owner and repo from repo_url
    match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/?$", repo_url)
    if match:
        owner = match.group(1)
        repo_name = match.group(2)
    else:
        return {
            "error": True,
            "message": "Invalid GitHub repository URL format. Expected: https://github.com/owner/repo",
            "input_repo_url": repo_url 
        }

    # 2. Validate and convert issue_number
    try:
        issue_num_int = int(issue_number)
        if issue_num_int <= 0:
            raise ValueError("Issue number must be a positive integer.")
    except ValueError:
        return {
            "error": True,
            "message": "Invalid issue number. It must be a string representing a positive integer.",
            "input_issue_number": issue_number
        }

    # 3. Construct the URL for the FastAPI endpoint
    api_endpoint_url = f"{root_url}/api/v1/github/issue-context/{owner}/{repo_name}/{issue_num_int}"

    # 4. Call the FastAPI endpoint
    try:
        response = requests.get(api_endpoint_url, timeout=30) # 30-second timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()

    except Exception as e:
        # Log the detailed error on the server side for debugging
        error_log_message = (
            f"MCP tool 'get_issue_context' failed for {owner}/{repo_name}#{issue_num_int}. "
            f"Error calling internal API ({api_endpoint_url}): {type(e).__name__} - {str(e)}."
        )
        if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
            error_log_message += f" Response from API: {e.response.text}"
        print(error_log_message) # Server-side log

        # Generic error message for the AI
        return {
            "error": True,
            "message": (
                f"Could not retrieve context for issue '{issue_num_int}' in repository '{owner}/{repo_name}'. "
                "Please ensure the repository URL and issue number are correct. "
                "If the problem persists, the backend service might be experiencing issues."
            )
        }

@mcp.resource("ghsb://digest/{repo_owner}/{repo_name}")
def get_processed_repo(repo_owner: str, repo_name: str) -> str | dict:
    """Get repository that was processed and stored.

    Args:
        repo_owner: a GitHub username of the repo owner
        repo_name: the name of the GitHub repository

    Return:
        str: the file containing processed data
    """
    repo_url = f"https://github.com/{repo_owner}/{repo_name}"
    payload = {
        "repo_url": repo_url
    }
    url = f"{root_url}/api/v1/process"
    response = requests.post(url, json=payload)
    data = response.json()
    # wait for response, and get the filename
    if "output_path" in data:
        output_path = data["output_path"]
        # then search in data folder for that file and return the content
        with open(output_path, "r", encoding='utf-8') as file:
            content = file.read()
        return content if content else None
    
    return {"message": data["message"]}

if __name__ == "__main__":
    print("MCP Server script starting...", file=sys.stderr)

    # Check for the crucial environment variable
    fastapi_url = os.environ.get("GHSB_API_ENDPOINT")
    if not fastapi_url:
        print("ERROR: FASTAPI_SERVICE_URL environment variable not set!", file=sys.stderr)
        sys.exit(1) # Exit if critical config is missing
    print(f"MCP Server configured to use FastAPI at: {fastapi_url}", file=sys.stderr)

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