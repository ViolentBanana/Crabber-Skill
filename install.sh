#!/bin/bash
set -e

echo "🦀 开始安装 Crabber Skill..."

# Define paths
CRABBER_HOME="$HOME/.crabber"
VENV_DIR="$CRABBER_HOME/venv"
BIN_DIR="$CRABBER_HOME/bin"
PUBLIC_DIR="$CRABBER_HOME/public/share"
HERMES_SKILLS_DIR="$HOME/.hermes/skills"

# 1. Create directories
echo "📁 创建目录结构..."
mkdir -p "$CRABBER_HOME"
mkdir -p "$BIN_DIR"
mkdir -p "$PUBLIC_DIR"

# 2. Copy core files
echo "📦 复制核心文件..."
cp -R core "$CRABBER_HOME/"
cp core/crabber_cli.py "$BIN_DIR/crabber"
chmod +x "$BIN_DIR/crabber"

# 3. Setup Virtual Environment
echo "🐍 设置 Python 虚拟环境..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# 4. Install dependencies
echo "📦 安装依赖 (FastAPI, Uvicorn, Jinja2)..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet fastapi uvicorn pydantic jinja2

# 5. Setup Hermes Integration
if [ -d "$HERMES_SKILLS_DIR" ]; then
    echo "🔗 安装 Hermes Skill..."
    cp integrations/hermes/crabber.py "$HERMES_SKILLS_DIR/"
else
    echo "⚠️ 未检测到 Hermes skills 目录 ($HERMES_SKILLS_DIR)，跳过 Hermes 自动安装。"
    echo "如需手动安装，请将 integrations/hermes/crabber.py 复制到您的 Hermes skills 目录。"
fi

# 6. Add to PATH instruction
echo ""
echo "✅ Crabber 安装成功！"
echo "=========================================="
echo "要能够在终端直接使用 crabber 命令，请将以下行添加到您的 ~/.zshrc 或 ~/.bash_profile 中："
echo "export PATH=\"\$HOME/.crabber/bin:\$PATH\""
echo "=========================================="
echo ""
echo "💡 小龙虾 (OpenClaw) 用户："
echo "请参考 integrations/openclaw/plugin.json 进行配置接入。"
echo ""
