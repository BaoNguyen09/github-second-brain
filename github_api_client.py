import httpx
import os
from typing import List, Optional, Dict, Any

class GitHubApiError(Exception):
    """Custom exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

async def fetch_issue_context(
    owner: str,
    repo: str,
    issue_number: int,
    http_client: httpx.AsyncClient,
    github_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetches the title, body, state, and comments for a given GitHub issue.

    Args:
        owner: The owner of the GitHub repository.
        repo: The name of the GitHub repository.
        issue_number: The number of the issue.
        http_client: An instance of httpx.AsyncClient for making requests.
        github_token: Optional GitHub API token for authentication.

    Returns:
        A dictionary containing the structured issue context.

    Raises:
        GitHubApiError: If there's an issue communicating with the GitHub API
                        or if the response is unexpected.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    issue_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    issue_data_raw: Dict[str, Any] = {}
    comments_data_raw: List[Dict[str, Any]] = []

    try:
        # 1. Fetch the main issue details
        issue_response = await http_client.get(issue_url, headers=headers)
        
        if issue_response.status_code != 200:
            raise GitHubApiError(
                message=f"Error fetching issue {owner}/{repo}#{issue_number} from GitHub.",
                status_code=issue_response.status_code,
                details=issue_response.json()
            )
        issue_data_raw = issue_response.json()

        # 2. Fetch comments if the issue has any and comments_url is present
        comments_url = issue_data_raw.get("comments_url")
        if issue_data_raw.get("comments", 0) > 0 and comments_url:
            # For simplicity, fetching only the first page (up to 100 comments).
            # Implement pagination for all comments later in prod.
            comments_api_response = await http_client.get(comments_url, headers=headers, params={"per_page": 100})
            if comments_api_response.status_code == 200:
                comments_data_raw = comments_api_response.json()
            else:
                # Log a warning but don't fail the whole operation if comments can't be fetched
                print(f"Warning: Could not fetch comments for issue {owner}/{repo}#{issue_number}. Status: {comments_api_response.status_code}")
        
        # 3. Structure the required data based on "must-have" fields
        # Ensure user object and its login exist
        user_data = issue_data_raw.get("user", {})
        user_login = user_data.get("login")
        user_html_url = user_data.get("html_url")

        if not user_login:
            raise GitHubApiError(message="User login not found in issue data.", details=issue_data_raw)

        # Prepare comments list
        structured_comments = []
        for comment_raw in comments_data_raw:
            comment_user_data = comment_raw.get("user", {})
            comment_user_login = comment_user_data.get("login")
            comment_user_html_url = comment_user_data.get("html_url")
            if comment_user_login: # Only include comments with a valid user
                structured_comments.append({
                    "user": {"login": comment_user_login, "html_url": comment_user_html_url},
                    "created_at": comment_raw.get("created_at"),
                    "body": comment_raw.get("body", ""), # Ensure body is not None
                    "html_url": comment_raw.get("html_url")
                })

        return {
            "number": issue_data_raw.get("number"),
            "title": issue_data_raw.get("title"),
            "body": issue_data_raw.get("body"),
            "state": issue_data_raw.get("state"),
            "html_url": issue_data_raw.get("html_url"),
            "user": {"login": user_login, "html_url": user_html_url},
            "created_at": issue_data_raw.get("created_at"),
            "comments_count": issue_data_raw.get("comments", 0),
            "comments": structured_comments,
        }

    except httpx.RequestError as e:
        raise GitHubApiError(message=f"HTTP request to GitHub failed: {str(e)}", status_code=503) # Service Unavailable
    except KeyError as e:
        raise GitHubApiError(message=f"Unexpected data structure from GitHub API: missing key {str(e)}.", details=issue_data_raw)
    except Exception as e: # Catch any other unexpected error during processing
        raise GitHubApiError(message=f"An unexpected error occurred while processing GitHub data: {str(e)}")

