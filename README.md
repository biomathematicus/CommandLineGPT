
## README.md for OpenAI.NET: Minimalist Access to AI Agents in Python

### Overview

This repository offers a compact collection of Python tools to help developers interact with AI agents such as OpenAI's GPT and Anthropic's Claude. The interfaces include command-line shells, GUI widgets, and file-driven workflows. All scripts are configured to operate using standard environmental variable credentials, and they support API-based, conversational, and document-processing tasks.

### Git Protocol

After you make your changes:

```bash
git pull
git add .
git commit -m "[description of the change]"
git push
```

To set up Git credentials:

```bash
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

To undo a staged change:

```bash
git reset
```

To discard local changes and sync with the remote:

```bash
git reset --hard HEAD
```

### Prerequisites

* Python 3.x
* An OpenAI API key loaded via `OPENAI_API_KEY`
* An Anthropic API key loaded via `ANTHROPIC_API_KEY`
* (Optional) NLTK tokenizers: `python -c "import nltk; nltk.download('punkt')"`

### Installation

Clone the repository and run any of the scripts directly.

```bash
git clone [your-repo-url]
cd [your-repo]
python [script].py
```

### File Descriptions

* `ClaudeChat.py`: Basic terminal-based loop that sends user input to Anthropic Claude using `claude-3-opus-20240229`. It resets context on each input.

* `ClaudeChatUL.py`: Extension of `ClaudeChat.py` that allows users to upload PDF files. The text of the PDF is extracted and included in the prompt for Claude to analyze.

* `ClaudeGUI.py`: GUI front-end for Claude using PyQt5. Users can enter queries or drag-and-drop PDF files. The text is sent to Claude and the responses appear in a scrollable widget.

* `ClaudeQA.py`: Minimal one-off query example to Claude, used to test isolated questions. Uses `claude-3-sonnet-20240229`.

* `CommandLineGPT.code-workspace`: VS Code workspace configuration file for managing project layout and environment.

* `config.json`: Central configuration file that defines model names, instruction prompts, and interface identity for the assistant (e.g., Pepito Perez).

* `editJSON.py`: PyQt5-based interactive JSON tree editor that allows viewing, editing, saving, and modifying hierarchical JSON data structures with context menus and font controls.

* `generateSummaries.py`: Batch-processing script that traverses a directory of PDFs, extracts text using PyPDF2, summarizes each using the TextRank algorithm from `sumy`, and writes the results into a formatted JSON structure.

* `GrogChat.py`: CLI tool using LangChain and Groq's LLaMA-based API. It demonstrates integration of memory buffers and template prompts to carry out conversational interactions.

* `Helper.py`: Main CLI driver for interacting with OpenAI GPT agents. Supports uploading files, maintaining a thread, attaching files to conversations, and invoking OpenAI Assistant runs.

* `HelperGUI.py`: GUI version of `Helper.py` using PyQt5. Offers a text input box, assistant display window, drag-and-drop file upload, and clipboard support for copying the latest AI response.

* `README.md`: This file.

### License

This project is open-sourced under CC-BY-SA.

### Contact

For queries or suggestions, contact biomathematicus (Google it) or raise an issue in the repository.
