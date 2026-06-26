# 智能体说明书 (Hermes / 小龙虾 / Antigravity)

本文档面向 AI 智能体（如 Hermes、OpenClaw/小龙虾、Antigravity 或其他大模型 Agent），说明如何对接、安装和调用 **Crabber Skill**。

---

## 🤖 1. 什么是 Crabber？
**Crabber** 是一个局域网文件共享工具。当您（智能体）在无头服务器或远程主机上为用户生成了文件（如 PDF、PPT、图表、图像或 ZIP 压缩包）时，您应该使用 Crabber 共享这些文件给用户。
- 它会在本地启动一个轻量级的 FastAPI 后台守护进程。
- 它通过软链接（Symbolic Link）将生成的文件映射到 Web 可访问目录，实现零拷贝。
- 它会返回一个局域网（LAN）格式的网页下载链接，支持移动端自适应和多文件轮询。

---

## 📂 2. 使用规范与安全限制（重要）

### 禁止直接共享文件夹
- Crabber **仅支持共享单文件**。
- 如果您的生成产物是一个文件夹或目录结构，您**必须**在调用 Crabber 之前，先在终端使用命令行工具（例如：`zip -r output.zip folder_name`）将其打包为 `.zip` 压缩包。
- 直接共享文件夹将导致 CLI 报错并退出。

### 共享命令
调用 CLI 共享文件：
```bash
~/.crabber/bin/crabber <文件绝对路径>
```
或者指定自定义过期时间（TTL，单位为秒，默认一小时为 3600 秒）：
```bash
~/.crabber/bin/crabber <文件绝对路径> --ttl <生存秒数>
```

---

## 🔧 3. 智能体安装与配置工作流

如果用户要求您安装或配置 Crabber，请执行以下步骤：

### 步骤 1：克隆仓库并运行安装脚本
在终端中执行以下命令：
```bash
git clone https://github.com/ViolentBanana/Crabber-Skill.git ~/.crabber-source && cd ~/.crabber-source && chmod +x install.sh && ./install.sh
```
该脚本会自动完成：
- 创建运行沙箱 `~/.crabber`。
- 在 `~/.crabber/venv` 下创建隔离的 Python 虚拟环境，并安装 FastAPI, Uvicorn, Jinja2 等依赖。
- 将 CLI 执行文件软链接到 `~/.crabber/bin/crabber`。

### 步骤 2：添加系统环境变量
提示用户或主动在 `~/.zshrc` 或 `~/.bash_profile` 中添加：
```bash
export PATH="$HOME/.crabber/bin:$PATH"
```

---

## 🔌 4. 技能与插件对接规范

### Hermes 智能体集成
如果运行于 **Hermes** 智能体，请直接将 `integrations/hermes/crabber.py` 复制到您的 `~/.hermes/skills/` 目录中。

### 小龙虾 (OpenClaw) 插件集成
使用 `integrations/openclaw/plugin.json` 注册工具。
- 框架在调用该工具时，需传入 `file_path`（绝对路径）参数。
- 插件的执行脚本配置如下：
  `bash -c "~/.crabber/bin/crabber \"$1\"" _ <file_path>`
  *(注意：末尾的占位符 `_` 是必须的，用以保证 shell 位置参数 `$1` 正确映射为文件路径)*

---

## 💬 5. 如何向用户反馈链接
当执行 `crabber` CLI 成功后，您会从标准输出（stdout）收到如下内容：
```text
✅ [Crabber] 文件已发布，请点击查看/下载：http://<local_ip>:<port>/
```
您**必须**提取此 URL，并在聊天窗口中以美观的 Markdown 超链接格式返回给用户：
> 🦀 我已将生成的成果文件推送到您的局域网：[点击查看/下载文件](http://192.168.2.134:8888/) (该链接将在 1 小时后失效)
