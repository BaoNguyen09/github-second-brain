import sys
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

    while page_num <= MAX_PAGES_TO_FETCH:
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
    structured_comments: List[Dict[str, Any]] = []

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

def _build_hierarchical_tree(flat_tree_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Converts a flat list of GitHub tree entries into a hierarchical
    nested dictionary structure.
    """
    tree_root: Dict[str, Any] = {}
    for item in flat_tree_list:
        path_parts = item.get("path", "").split('/')
        current_level = tree_root
        for i, part in enumerate(path_parts):
            if not part: # Should not happen with valid GitHub paths
                continue
            
            is_last_part = (i == len(path_parts) - 1)
            
            if is_last_part:
                # It's a file or an explicitly listed empty directory from the flat list
                current_level[part] = {"_type": item.get("type", "blob")} # 'blob/file' or 'tree/dir'
            else:
                # It's a directory segment in the path
                if part not in current_level:
                    current_level[part] = {"_type": "tree", "children": {}}
                elif "_type" not in current_level[part] or current_level[part]["_type"] not in ("tree", "dir"):
                    # This case handles if a file and directory have the same prefix,
                    # though unlikely with standard git structures. Prioritize tree structure.
                    current_level[part] = {"_type": "tree", "children": {}}
                
                # Ensure 'children' exists if we are treating 'part' as a tree
                if "children" not in current_level[part]:
                     current_level[part]["children"] = {}

                current_level = current_level[part]["children"]
    return tree_root

def _format_tree_recursively(
    tree_node: Dict[str, Any],
    current_prefix: str,
    lines_list: List[str],
    current_depth: int,
    max_depth: Optional[int]
):
    """
    Recursively traverses the hierarchical tree and formats it into a list of strings.
    """
    if max_depth is not None and current_depth >= max_depth:
        return

    # Sort items: directories first (by type), then alphabetically by name
    # GitHub API usually returns items sorted, but explicit sort is safer.
    sorted_item_names = sorted(tree_node.keys())
    
    for i, name in enumerate(sorted_item_names):
        item_data = tree_node[name]
        is_last_child = (i == len(sorted_item_names) - 1)
        
        connector = "└── " if is_last_child else "├── "
        line = current_prefix + connector + name
        
        is_directory = item_data.get("_type") == "tree"
        if is_directory:
            line += "/" # Add trailing slash for directories
        
        lines_list.append(line)
        
        if is_directory and "children" in item_data and item_data["children"]:
            new_prefix = current_prefix + ("    " if is_last_child else "│   ")
            _format_tree_recursively(
                item_data["children"],
                new_prefix,
                lines_list,
                current_depth + 1,
                max_depth
            )

def format_github_tree_structure(
    flat_tree_list: List[Dict[str, Any]],
    repo_name_with_owner: str, # e.g., "baonguyen09/github-second-brain"
    max_depth: Optional[int] = None
) -> str:
    """
    Formats a flat list of GitHub tree entries into a human-readable,
    indented tree structure string, with optional depth control.

    Args:
        flat_tree_list: The list of tree entries from GitHub API
                        (e.g., from fetch_recursive_tree_from_github).
        repo_name_with_owner: The name of the repository (e.g., "owner/repo") to use as the root.
        max_depth: Optional maximum depth to display the tree.
                   Depth 0 means only the root repo name.
                   Depth 1 means root repo name and its direct children.
                   None means full depth.

    Returns:
        A string representing the formatted directory tree.
    """
    if not flat_tree_list:
        return f"Directory structure:\n└── {repo_name_with_owner}/\n    (Repository is empty or tree data not available)"

    hierarchical_tree = _build_hierarchical_tree(flat_tree_list)
    
    lines = ["Directory structure:"]
    
    # Handle max_depth for the root line itself
    if max_depth is not None and max_depth < 0: # Or treat 0 as only root
        lines.append(f"└── {repo_name_with_owner}/")
        return "\n".join(lines)

    lines.append(f"└── {repo_name_with_owner}/")
    
    # The children of the root are at depth 0 for _format_tree_recursively
    # So, if max_depth is 1, we want _format_tree_recursively to process current_depth 0.
    # The max_depth for the recursive formatter should be relative to the repo root's children.
    effective_max_depth_for_children = None
    if max_depth is not None:
        effective_max_depth_for_children = max_depth -1 # if max_depth=1, children_depth=0

    _format_tree_recursively(
        tree_node=hierarchical_tree,
        current_prefix="    ", # Initial indent for children of the root
        lines_list=lines,
        current_depth=0, # Children of root are at depth 0 of the repo content tree
        max_depth=effective_max_depth_for_children
    )
    
    return "\n".join(lines)

async def fetch_directory_tree_with_depth(
    owner: str,
    repo: str,
    http_client: httpx.AsyncClient,
    ref: Optional[str] = None,
    github_token: Optional[str] = None,
    depth: Optional[int] = 1,
    full_depth: Optional[bool] = False,
) -> str:
    """
    Fetch the tree from github and format it to be LLM-friendly

    Args:
        owner: The owner of the GitHub repository
        repo: The name of the GitHub repository
        http_client: An instance of httpx.AsyncClient for making requests
        ref: Branch name, tag, or commit SHA of specified tree
        github_token: Optional GitHub API token for authentication
        depth: The specified depth of the tree in int
        full_depth: Boolean for fetching tree with full depth

    Returns:
        A string representing the formatted directory tree.

    Raises:
        GitHubApiError: If there's an issue communicating with the GitHub API
                        or if the response is unexpected.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    # 1. Get the ref to use (default branch if None)
    if not ref: # fetch repo info to get defaul branch name
        repo_info_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            repo_info_resp = await http_client.get(repo_info_url, headers=headers)
            repo_info_resp.raise_for_status()
            ref = repo_info_resp.json().get("default_branch", "main") # Fallback to main if somehow not found
        except Exception as e:
            raise GitHubApiError(
                message=f"Failed to fetch default branch for {owner}/{repo}: {str(e)}",
                status_code=getattr(e, 'response', None) and getattr(e.response, 'status_code', None)
            ) from e

    # 2. Get the tree recursively
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"

    print(f"Fetching tree from: {tree_url}", file=sys.stderr)
    try:
        tree_resp = await http_client.get(tree_url, headers=headers)
        
        if tree_resp.status_code == 404:
             # This can happen if the ref (branch/tag/commit/tree_sha) doesn't exist
             # or if the repository itself is not found or is private without auth.
            raise GitHubApiError(
                message=f"Tree or ref '{ref}' not found for {owner}/{repo}. Or repository is private/inaccessible.",
                status_code=404,
                details=tree_resp.text
            )
        if tree_resp.status_code == 409: # Conflict - often for empty repository
            print(f"Warning: Received 409 Conflict for tree {owner}/{repo}@{ref}. Likely an empty repository. Returning empty tree.", file=sys.stderr)
            return []

        tree_resp.raise_for_status() # For other HTTP errors
        
        tree_data = tree_resp.json()

        if tree_data.get("truncated"):
            print(f"Warning: Tree data for {owner}/{repo}@{ref} was truncated by GitHub API. The returned list might be incomplete.", file=sys.stderr)

        return format_github_tree_structure(tree_data["tree"], f"{owner}/{repo}", max_depth=None if full_depth else depth)

    except httpx.HTTPStatusError as e:
        raise GitHubApiError(
            message=f"GitHub API HTTP error fetching tree for {owner}/{repo}@{ref}: {e.response.status_code}",
            status_code=e.response.status_code,
            details=e.response.text
        ) from e
    except httpx.RequestError as e:
        raise GitHubApiError(message=f"HTTP request failed while fetching tree for {owner}/{repo}@{ref}: {str(e)}") from e
    except Exception as e: # Catch-all for other unexpected errors like JSON decoding
        raise GitHubApiError(message=f"An unexpected error occurred while fetching tree for {owner}/{repo}@{ref}: {str(e)}") from e
    
async def fetch_file_contents(
    owner: str,
    repo: str,
    path: str,
    http_client: httpx.AsyncClient,
    ref: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Optional[str]:
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
            print(f"File/Directory not found: {path} in {owner}/{repo}@{ref or 'default branch'}", file=sys.stderr)
            return None 
        response.raise_for_status()
        returned_content_type = response.headers["Content-Type"]

        if returned_content_type == "application/json; charset=utf-8": # this is a dir, so format it and return
            data = response.json()
            return format_github_tree_structure(data, f"{owner}/{repo}", None)
        # else it's a raw text of file content
        return response.text

    except httpx.HTTPStatusError as e:
        print(f"GitHub API error fetching file/directory {path}@{ref or 'default'}: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        raise GitHubApiError(f"GitHub API error: {e.response.status_code}", status_code=e.response.status_code, details=e.response.text) from e
    except Exception as e:
        print(f"Error fetching or decoding file/directory {path}@{ref or 'default'}: {e}", file=sys.stderr)
        raise GitHubApiError(f"Failed to process contents: {str(e)}") from e
    