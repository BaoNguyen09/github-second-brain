<!-- PROJECT LOGO -->
<div align="center">
  <a href="https://github.com/BaoNguyen09/github-second-brain">
    <img src="assets/images/ghsb_logo_v1.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">GitHub Second Brain</h3>

  <p align="center">    
    A developer partner for navigating and understanding any GitHub repositories for deep insights into codebase, history, and project context.
    <br />
    <a href="https://github.com/BaoNguyen09/github-second-brain"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://drive.google.com/file/d/1PhLqO4N2nWrZi89p7QG4enUO7agBe8tK/view?usp=sharing">View Demo</a>
    &middot;
    <a href="https://github.com/BaoNguyen09/github-second-brain/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/BaoNguyen09/github-second-brain/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

## ✨ Features
* 😎 **Latest Documentation on ANY GitHub Project**: Grant your AI assistant seamless access to the GitHub project's documentation and code. The built-in retrieval tools help the AI gets tree directory and specific file content without exceeding Context Window Limit!
* 🧠 **No More Hallucinations**: With Github Second Brain, your AI assistant can provide accurate and relevant answers to your questions.
* ✅ **Open, Free, and Private**: Github Second Brain is open-source and completely free to use. It doesn't collect personal information or store queries. You can even self-host it!

<!-- GETTING STARTED -->
## Getting Started
Currently, this project isn't deployed on the cloud so you have to run it locally to use it.

## ⚙️ Prerequisites
Before you begin, ensure you have met the following requirements:
* You have installed [uv](https://github.com/astral-sh/uv) (for environment and package management).
* You have installed Python (uv will typically manage Python versions or use an existing compatible one, Python 3.8+ is recommended).
* Primarily tested on Windows. Linux and Mac compatibility is currently untested but may work.
* You have read the [FastAPI documentation](https://fastapi.tiangolo.com/) (recommended).

## 🚀 Installation
To run this server locally, follow these steps:

1. Clone the repository
```bash
git clone https://github.com/BaoNguyen09/github-second-brain.git
cd github-second-brain
```

2. Install dependencies

Firstly, create a virtual environment for this project if you don't currently have. This will create a `.venv` directory.
```bash
uv venv
```
Secondly, activate it:
  * On Windows (PowerShell):
```powershell
venv\Scripts\activate
```
  * On macOS and Linux (bash/zsh):
```bash
source .venv/bin/activate
```

## 🎮 Usage
After installation, you need to run both the FastAPI server and the MCP server:
1.  **Start the FastAPI API server:**
    Open a terminal (with the virtual environment activated), navigate to the project root directory, and run:
    ```bash
    fastapi dev
    ```
    This server handles the repository processing and file serving. By default, it will be accessible at http://127.0.0.1:8000.

2.  **Start the MCP server:**
    Open a *new* terminal (with the virtual environment activated), navigate to the project root directory, and run:
    ```bash
    mcp dev mcp_server.py
    ```
    This script utilizes the MCP library to start the server and provide the tools for your AI client. It connects to the FastAPI server to get the necessary data. The `mcp[cli]` package you have in `requirements.txt` provides the necessary components for this script to run. By default, the mcp inspector will be accessible at http://127.0.0.1:5173 for the client UI (and port 3000 for the MCP proxy server)

3. **Connect your AI assistant**
<details>
  <summary>Select your AI assistant from the options below and follow the configuration instructions:</summary>
  
  #### Connecting Cursor
  
  Update your Cursor configuration file at `~/.cursor/mcp.json`:
  ```json
     {
       "mcpServers": {
         "github-second-brain": {
            "command": "uv",
            "args": [
                "--directory",
                "path\\to\\your\\folder",
                "run",
                "mcp_server.py"
            ]
        },
       }
     }
  ```
  
  #### Connecting Claude Desktop
  
  1. In Claude Desktop, go to Settings > Developer > Edit Config
  2. Replace the configuration with:
  ```json
     {
       "mcpServers": {
        "github-second-brain": {
            "command": "uv",
            "args": [
                "--directory",
                "path\\to\\your\\folder",
                "run",
                "mcp_server.py"
            ]
        },
       }
     }
  ```
</details>

<!--
## ⚙ How It Works
Github Second Brain connects your AI assistant to GitHub repositories using the Model Context Protocol (MCP), a standard that lets AI tools request additional information from external sources.
What happens when you use Github Second Brain:
1. **You provide the GitSB URL** to your AI assistant (e.g., `ghsb.com/microsoft/typescript`). GitSB exposes tools like documentation fetching, smart search, code search, etc.
2. **Prompt the AI assistant** on documentation/code-related questions.
3. **Your AI sends requests** to GitSB to use its tools (with your approval).
4. **GitSB executes the AI's request** and returns the requested data.
5. **Your AI receives the information** and generates a more accurate, grounded response without hallucinations.
-->

## 🗺️ Roadmap
We are continuously working to improve [GitHub Second Brain]. Here are some of our planned features:

- [x] ~~Add a mcp tool to retrieve specific file content and tree directory~~
- [ ] Add a mcp tool to trieve github issues + pull request
- [ ] Change the current gitingest processing to async

For a more detailed view of our upcoming features and to suggest new ones, please see the open issues and our project board (optional).

## 🤝 Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

### Non-technical ways to contribute
- **Give the project a star⭐!**: This will help make the project better for you because it will increase the project reliability and visibility which attracts more contributor to improve this project.
- **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/BaoNguyen09/github-second-brain/issues/new) on GitHub. This will help us track and prioritize your request.
- **Spread the Word**: If you like GitHub Second Brain, please share it with your friends, colleagues, and on social media. This will help us grow the community and make it even better.
- **Use GitHub Second Brain**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/BaoNguyen09/github-second-brain/issues/new) on GitHub or by reaching out to me: `thienbao05@arizona.edu` .

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

### `get_processed_repo`

This tool gives AI the entire codebase ingested into one prompt-friendly text file. It works by ingesting the entire codebase with gitingest library and serving it directly. This gives the AI a good comprehensive look of what the project is about. However, this tool isn't recommended and will soon be disabled because it can easily overflow AI with data, exceeding its Context Window Limit.

**When it's useful:** For small repos, and to ask any types of questions: overview of the repo, how to contribute, etc.

### `get_tree_directory`

This tool gives AI the full tree directory of the codebase in plaintext with indentation. Instead of loading all the documentation (which could be very large), it can use this to understand the overview of the repo, and then use other tools to retrieve relevant parts only.

**When it's useful:** For questions about the structure of the repositories.

### `get_file_content`

This tool returns full content of any files visible in the tree directory in plaintext.

**When it's useful:** For specific questions about particular features, functions, concepts within a project, or any technical details not coverted in the documentation.


## 💬 Support & Community
If you have questions, need support, or want to connect with the Github Second Brain community, here are some resources:

Issue Tracker: For bug reports and feature requests, please use GitHub Issues.

## 📝 License
This project is licensed under the [Apache License 2.0](LICENSE).

## 🙏 Acknowledgments
We would like to thank the following individuals and projects for their contributions and inspiration:

- Gitingest for the underlying tool.
- GitMCP for reference and setting the standards.
- All our amazing contributors!

## Disclaimer
Github Second Brain is provided "as is" without warranty of any kind. While we strive to ensure the reliability and security of our service, we are not responsible for any damages or issues that may arise from its use. GitHub projects accessed through Github Second Brain are subject to their respective owners' terms and conditions. Github Second Brain is not affiliated with GitHub or any of the mentioned AI tools.
