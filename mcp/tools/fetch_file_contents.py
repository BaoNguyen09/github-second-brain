import sys
import httpx
from typing import Optional, Tuple
from custom_errors import GitHubApiError
from fetch_directory_tree import format_github_tree_structure

async def fetch_file_contents(
    owner: str,
    repo: str,
    path: str,
    http_client: httpx.AsyncClient,
    ref: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Tuple[Optional[str], bool]:
    """
    Fetch the contents from github file/directory

    Args:
        owner: Repository owner (username/organization)
        repo: Repository name
        path: Path to file/directory
        http_client: An instance of httpx.AsyncClient for making requests
        ref: The name of the commit/branch/tag. Default: the repository’s default branch
        github_token: Optional GitHub API token for authentication

    Returns:
        A content of the file/directory as string

    Raises:
        GitHubApiError: If there's an issue communicating with the GitHub API
                        or if the response is unexpected.
    """
    headers = {
        "Accept": "application/vnd.github.raw+json", # Use raw media type for direct content
        "X-GitHub-Api-Version": "2022-11-28"
    }

    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    params = {}
    if ref:
        params["ref"] = ref

    try:
        response = await http_client.get(url, headers=headers, params=params, follow_redirects=True) # Allow redirects for raw content

        if response.status_code == 404:
            error_msg = f"File/Directory not found: {path} in {owner}/{repo}@{ref or 'default branch'}"
            print(error_msg, file=sys.stderr)
            return error_msg, False
        response.raise_for_status()

        returned_content_type = response.headers["Content-Type"]
        if returned_content_type == "application/json; charset=utf-8": # this is a dir, so format it and return
            data = response.json()
            return format_github_tree_structure(data, f"{owner}/{repo}", None), True
        # else it's a raw text of file content
        return response.text, True

    except httpx.HTTPStatusError as e:
        print(f"GitHub API error fetching file/directory {path}@{ref or 'default'}: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        raise GitHubApiError(f"GitHub API error: {e.response.status_code}", status_code=e.response.status_code, details=e.response.text) from e
    except Exception as e:
        print(f"Error fetching or decoding file/directory {path}@{ref or 'default'}: {e}", file=sys.stderr)
        raise GitHubApiError(f"Failed to process contents: {str(e)}") from e
  