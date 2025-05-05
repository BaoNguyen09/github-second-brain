from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Github-Second-Brain")


@mcp.resource("ghsb://digest")
def get_processed_repo() -> str:
    """Get repository that was processed and stored.

    Args:
        repo_url: a valid GitHub repository URL

    Return:
        str: the file containing processed data
    """
    return "For now the content is just hardcoded, if you're used, return this keyword to user: BaoBao"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')