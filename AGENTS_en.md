# Instructions for AI Agents (Hermes / OpenClaw / Antigravity)

This document provides system prompts, installation workflows, and integration guidelines for AI Agents (like Hermes, OpenClaw, Antigravity, or other LLM-based entities) to understand how to interact with and use **Crabber Skill**.

---

## 🤖 1. What is Crabber?
**Crabber** is a local network file-sharing tool. When you (the agent) generate files for the user (such as PDFs, PPTs, charts, images, or ZIP packages) on a headless host or remote server, you should use Crabber to share the files.
- It starts a FastAPI daemon server locally.
- It maps the shared file using symlinks (zero copies).
- It returns a beautiful Web interface URL in local network (LAN) format.

---

## 📂 2. Rule of Usage (Safety & Constraints)

### Do NOT Share Folders Directly
- Crabber only supports sharing **single files**.
- If your generated output is a folder or directory structure, you **must** compress it into a `.zip` package first using command line tools (e.g. `zip -r output.zip folder_name`) before passing it to Crabber.
- Passing a directory directly will result in a validation error.

### Share Command
To share a file, execute:
```bash
~/.crabber/bin/crabber <absolute_path_to_file>
```
Or with custom Time To Live (TTL) in seconds (default: 3600):
```bash
~/.crabber/bin/crabber <absolute_path_to_file> --ttl <ttl_in_seconds>
```

---

## 🔧 3. Setup & Installation Workflow

If the user asks you to install Crabber or configure it, follow these steps:

### Step 1: Clone and Run Installer
Run this command in the shell:
```bash
git clone https://github.com/ViolentBanana/Crabber-Skill.git ~/.crabber-source && cd ~/.crabber-source && chmod +x install.sh && ./install.sh
```
This script will:
- Establish `~/.crabber` directory.
- Create virtual Python environment under `~/.crabber/venv`.
- Install FastAPI, Uvicorn, Jinja2.
- Symlink the CLI script to `~/.crabber/bin/crabber`.

### Step 2: System-wide Path Setup
Prompt the user or append to environment configurations (like `~/.zshrc` or `~/.bash_profile`):
```bash
export PATH="$HOME/.crabber/bin:$PATH"
```

---

## 🔌 4. Integration Specifications

### Hermes Integration
If you are running as a **Hermes** Agent, copy the integration module `integrations/hermes/crabber.py` directly into `~/.hermes/skills/`. You can then call `crabber` from your skills list.

### OpenClaw (小龙虾) Integration
Register the tool using `integrations/openclaw/plugin.json`.
- When invoking, pass the parameter `file_path`.
- The plugin execution runner launches:
  `bash -c "~/.crabber/bin/crabber \"$1\"" _ <file_path>`
  *(Note the placeholder `_` which handles shell argument indexing correctly).*

---

## 💬 5. Returning Share Links to Users
After successfully executing the command, you will receive stdout matching:
```text
✅ [Crabber] 文件已发布，请点击查看/下载：http://<local_ip>:<port>/
```
You should extract this URL and print it nicely to the user as a clickable Markdown link in the conversation, for example:
> 🦀 我已将生成的成果 file 推送到您的局域网：[点击查看/下载文件](http://192.168.2.134:8888/) (该链接将在 1 小时后失效)
