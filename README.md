# GitHub Second Brain
_An MCP server that feeds your AI models any github repositories._
## Description
This MCP server processes github repo into an ai-friendly text format, and let MCP clients directly access and understand code context.
## More details
The database will host every processed repo by all users that any AI clients can directly access without a developer token. Each AI client can directly request the server to process any unprocessed repo, this repo will then be stored on database and is accessible to other AI clients.

Developer token is required if they want to process private repo or local repo.
