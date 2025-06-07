import sys
import httpx
from typing import List, Optional, Dict, Any
from custom_errors import GitHubApiError


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
   