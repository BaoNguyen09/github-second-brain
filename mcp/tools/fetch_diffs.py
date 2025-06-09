import sys
from typing import Optional, Any, Dict
import httpx

from tools.custom_errors import GitHubApiError

async def fetch_diffs(
    owner: str,
    repo: str,
    http_client: httpx.AsyncClient,
    github_token: Optional[str] = None,
    pr_number: Optional[int] = None,
    base_ref: Optional[str] = None,
    head_ref: Optional[str] = None
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
    if not pr_number and not (base_ref and head_ref):
        raise ValueError("Must provide either 'pr_number' or both 'base_ref' and 'head_ref'.")

    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    url = ""
    if pr_number:
        # For PRs, we get the diff directly from the pulls endpoint
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        print(f"Fetching diff for PR #{pr_number} from: {url}", file=sys.stderr)
    else:
        # For comparing branches/commits, we use the compare endpoint
        url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base_ref}...{head_ref}"
        print(f"Fetching diff between {base_ref}...{head_ref} from: {url}", file=sys.stderr)

    try:
        response = await http_client.get(url, headers=headers, timeout=60.0)
        
        # Check for errors after the request is made
        if response.status_code == 404:
            raise GitHubApiError(
                message=f"Not Found: The repository, PR, or refs could not be found.",
                status_code=404,
                details=response.text
            )
        response.raise_for_status() # Raise exception for other 4xx/5xx status codes
        
        return {
            "diff_content": response.text,
            "source": "pr" if pr_number else "compare",
            "pr_number": pr_number,
            "base_ref": base_ref,
            "head_ref": head_ref
        }

    except httpx.HTTPStatusError as e:
        raise GitHubApiError(
            message=f"GitHub API HTTP error: {e.response.status_code}",
            status_code=e.response.status_code,
            details=e.response.text
        ) from e
    except httpx.RequestError as e:
        raise GitHubApiError(f"HTTP request failed: {str(e)}") from e
    except Exception as e:
        raise GitHubApiError(f"An unexpected error occurred while fetching diff: {str(e)}") from e
