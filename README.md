<!-- PROJECT LOGO -->
<div align="center">
  <a href="https://github.com/BaoNguyen09/github-second-brain">
    <img src="assets/images/ghsb_logo_v1.png" alt="Logo" width="200" height="200">
  </a>

<h3 align="center">GitHub Second Brain</h3>

  <p align="center">    
    A set of tools that let AI explore github repos on-demand so it can better assist you.
    <br />
    <a href="https://github.com/BaoNguyen09/github-second-brain"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/BaoNguyen09/github-second-brain/issues/new?labels=bug&template=bug_report.md">Report Bug</a>
    &middot;
    <a href="https://github.com/BaoNguyen09/github-second-brain/issues/new?labels=enhancement&template=feature_request.md">Request Feature</a>
    &middot;
    <a href="https://github.com/BaoNguyen09/github-second-brain/issues/new?labels=question&template=question.md">Ask Question</a>
  </p>
</div>


## Recent Major Update
<details>


<summary> This project underwent a major refactor in June 8th, 2025 (https://github.com/baonguyen09/github-second-brain/issues/42). </summary>

- **Legacy version**: Available on `legacy/v1-archive` branch
- **Current version**: Main branch (v2.0+)
- **Migration guide**: See [MIGRATION.md](MIGRATION.md)

### Branch Information
- `main` - Current refactored version
- `legacy/v1-archive` - Original architecture (frozen)
  
</details>

## Project Launch
<video align="center" src="https://github.com/user-attachments/assets/ecb05256-8bb0-427c-b6c4-c7d93762bc67" width="80%"></video>

## Why?
### The Problem
When I first started contributing to an open-source project to gain more experience, the repo was just too big for a first-timer, and I felt completely overwhelmed. I wanted to use an AI assistant to help me navigate, but I had no good way to provide the necessary context.

### Solution
A self-hosted mcp server that gives an AI client a set of tools to explore and understand GitHub repos on its own.

## ✨ Features

* 😎 **Latest Documentation on ANY GitHub Project**: Grant your AI assistant seamless access to the GitHub project's documentation and code. The built-in retrieval tools help the AI gets tree directory and specific file content without exceeding Context Window Limit!

* 🧠 **No More Hallucinations**: With Github Second Brain, your AI assistant can provide accurate and relevant answers to your questions.

* ✅ **Open, Free, and Private**: Github Second Brain is open-source and completely free to use. It doesn't collect personal information or store queries. This is completely self-hosted!

* Extracting and analyzing data from GitHub repositories.

<!-- GETTING STARTED -->
## Getting Started

## ⚙️ Prerequisites
Before you begin, ensure you have met the following requirements:
1. To run the server in a container, you will need to have [Docker](https://www.docker.com/) installed.
2. Once Docker is installed, you will also need to ensure Docker is running. The image is public; if you get errors on pull, you may need to `docker logout ghcr.io`.
3. Lastly you will need to [Create a GitHub Personal Access Token](https://github.com/settings/personal-access-tokens/new).
The MCP server can use many of the GitHub APIs, so enable the permissions that you feel comfortable granting your AI tools (to learn more about access tokens, please check out the [documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)).


## 🚀 Installation

### Usage with Claude Desktop
  1. In Claude Desktop, go to Settings > Developer > Edit Config
  2. Replace the configuration with:
```json
{
  "mcpServers": {
    "github-second-brain": {
      "command": "docker",
      "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "GITHUB_PERSONAL_ACCESS_TOKEN",
          "ghcr.io/baonguyen09/github-second-brain:latest"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_PERSONAL_GITHUB_ACCESS_TOKEN"
      }
    }
  }
}
```

### Usage with Cursor
Update your Cursor configuration file at `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "github-second-brain": {
      "command": "docker",
      "args": [
          "run",
          "-i",
          "--rm",
          "-e",
          "GITHUB_PERSONAL_ACCESS_TOKEN",
          "ghcr.io/baonguyen09/github-second-brain:latest"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_PERSONAL_GITHUB_ACCESS_TOKEN"
      }
    }
  }
}
  ```

## ⚙ How It Works
Github Second Brain connects your AI assistant to GitHub repositories using the Model Context Protocol (MCP), a standard that lets AI tools request additional information from external sources.
What happens when you use Github Second Brain:
1. **You provide a [docker image](https://ghcr.io/baonguyen09/github-second-brain)** to your AI assistant that is used to build a local MCP server, exposing tools for fetching issue context, file content, directory tree, etc.
2. **Prompt the AI assistant** on documentation/code-related questions.
3. **Your AI sends requests** to the locally built MCP server to use its tools (with your approval).
4. **Local server executes the AI's request** and returns the requested data.
5. **Your AI receives the information** and generates a more accurate, grounded response without hallucinations.

## 🗺️ Roadmap
We are continuously working to improve GitHub Second Brain. Here are some of our planned features:

- [x] ~~Add a mcp tool to retrieve file contents and tree directory with specified depth~~
- [ ] Add a mcp tool to trieve ~~github issues~~ + pull request
- [x] ~~Change the current gitingest processing to directly use github api for faster response~~
- [x] ~~Change the architecture of the project to be completely self-hosted (data never leaves your machine)~~

For a more detailed view of our upcoming features and to suggest new ones, please see the open issues and our project board.

## 🤝 Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

### Non-technical ways to contribute
- **Give the project a star⭐!**: This will help make the project better for you because it will increase the project reliability and visibility which attracts more contributor to improve this project.
- **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/BaoNguyen09/github-second-brain/issues/new) on GitHub. This will help us track and prioritize your request.
- **Spread the Word**: If you like GitHub Second Brain, please share it with your friends, colleagues, and on social media. This will help us grow the community and make it even better.
- **Use GitHub Second Brain**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/BaoNguyen09/github-second-brain/issues/new) on GitHub or by reaching out to Bao: `thienbao05@arizona.edu` .

### Technical ways to contribute
If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

Please read our Contributing Guidelines for detailed instructions on how to contribute, our coding standards, and the pull request process. Also, please review our Code of Conduct to understand the community standards we uphold.

## 🛠️ Tools
Github Second Brain provides AI assistants with several valuable tools to help them access, understand, and query GitHub repositories.

### `get_processed_repo` (deprecated)

- This tool gives AI the entire codebase ingested into one prompt-friendly text file. It works by ingesting the entire codebase with gitingest library and serving it directly. This gives the AI a good comprehensive look of what the project is about. However, this tool isn't recommended and will soon be disabled because it can easily overflow AI with data, exceeding its Context Window Limit.

- **When it's useful:** For small repos, and to ask any types of questions: overview of the repo, how to contribute, etc.

### `get_tree_directory`

- This tool gives AI the full tree directory of the codebase in plaintext with indentation. Instead of loading all the documentation (which could be very large), it can use this to understand the overview of the repo, and then use other tools to retrieve relevant parts only.

- **When it's useful:** For questions about the structure of the repositories.

### `get_repo_contents`

- This tool returns full content of any files/directories existing in the repository.

- **When it's useful:** For specific questions about particular features, functions, concepts within a project, or any technical details not coverted in the documentation.

### `get_issue_context`

- This tool returns detailed context of any github issues including title, body, metadata, and all the comments within that issue.

- **When it's useful:** For questions related to a github issue and the context around it.

### `get_code_diff`

- This tool returns detailed diff of any github pull request, different branches, tags, and commits

- **When it's useful:** For questions related to a github pull request or code versions (between branches/tags/releases)

## 📝 License
This project is licensed under the [Apache License 2.0](LICENSE).

## 🙏 Acknowledgments
We would like to thank the following individuals and projects for their contributions and inspiration:

- GitMCP for reference
- Official GitHub MCP Server
- All our amazing contributors!

## Disclaimer
Github Second Brain is provided "as is" without warranty of any kind. While we strive to ensure the reliability and security of our service, we are not responsible for any damages or issues that may arise from its use. GitHub projects accessed through Github Second Brain are subject to their respective owners' terms and conditions. Github Second Brain is not affiliated with GitHub or any of the mentioned AI tools.
