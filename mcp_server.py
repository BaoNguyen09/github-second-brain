from mcp.server.fastmcp import FastMCP, Context
import requests

# Initialize FastMCP server
mcp = FastMCP("Github-Second-Brain")

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
    url = "http://127.0.0.1:8000/api/v1/process"
    response = requests.post(url, json=payload)
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
def get_directory_tree(repo_url: str) -> str:
    """Get directory tree of repository that was processed.

    Args:
        repo_url: a valid GitHub repository link

    Return:
        str: the full content of directory tree
    """

    payload = {
        "repo_url": repo_url
    }
    url = "http://127.0.0.1:8000/api/v1/dir-tree"
    response = requests.get(url, json=payload)
    data = response.json()

    # wait for response, and get the tree
    if data["message"] == "Success":
        return data["directory_tree"]
    
    return data["message"]

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
    url = "http://127.0.0.1:8000/api/v1/process"
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
    # Initialize and run the server
    mcp.run(transport='stdio')