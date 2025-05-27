import httpx
from typing import List, Optional, Dict, Any

class GitHubApiError(Exception):
    """Custom exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

async def _fetch_all_paginated_comments(
    start_url: str,
    http_client: httpx.AsyncClient,
    headers: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Fetches all items from a paginated GitHub API endpoint.
    """
    all_comments: List[Dict[str, Any]] = []
    base_comments_url: Optional[str] = start_url
    page_num = 1
    MAX_PAGES_TO_FETCH = 50

    while page_num < MAX_PAGES_TO_FETCH:
        request_url = f"{base_comments_url}?per_page=100&page={page_num}"
        
        print(f"Fetching comments page {page_num} from {request_url}") 
        try:
            response = await http_client.get(request_url, headers=headers)
            response.raise_for_status() # Raise an exception for 4xx/5xx errors
            
            current_page_items = response.json()
            if isinstance(current_page_items, list):
                if not current_page_items:
                    # Empty list means no more comments on this page or subsequent pages
                    print(f"Received empty list for page {page_num}. End of comments.")
                    break 
                all_comments.extend(current_page_items)
            else:
                # Should not happen for endpoints like comments list
                print(f"Warning: Expected a list from paginated endpoint {base_comments_url}, got {type(current_page_items)}")
                break 

            # If we fetched fewer than 100 items, it's likely the last page
            if len(current_page_items) < 100:
                print(f"Fetched {len(current_page_items)} items on page {page_num}, assuming end of comments.")
                break
            
            page_num += 1 # Prepare for the next page
        
        except httpx.HTTPStatusError as e:
            # Log error but allow partial data return if some pages were fetched
            print(f"HTTP error fetching page {page_num} from {base_comments_url}: {e}. Returning {len(all_comments)} items fetched so far.")
            break 
        except Exception as e:
            print(f"Unexpected error during pagination for {base_comments_url}: {e}. Returning {len(all_comments)} items fetched so far.")
            break # Stop on other errors too

    if page_num > MAX_PAGES_TO_FETCH:
        print(f"Warning: Reached MAX_PAGES_TO_FETCH ({MAX_PAGES_TO_FETCH}) for comments. Data might be incomplete.")

    print(f"Fetched a total of {len(all_comments)} comments over {page_num-1 if page_num > 1 else page_num} attempted page(s).")
    return all_comments

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
            comments_data_raw = await _fetch_all_paginated_comments(comments_url, http_client, headers=headers)

            if comments_data_raw:
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
            else:
                # Log a warning but don't fail the whole operation if comments can't be fetched
                print(f"Warning: Could not fetch comments for issue {owner}/{repo}#{issue_number}.")
        
        # 3. Structure the required data based on "must-have" fields
        # Ensure user object and its login exist
        user_data = issue_data_raw.get("user", {})
        user_login = user_data.get("login")
        user_html_url = user_data.get("html_url")

        if not user_login:
            raise GitHubApiError(message="User login not found in issue data.", details=issue_data_raw)

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

