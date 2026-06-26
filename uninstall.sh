#!/bin/bash
set -e

echo "🦀 开始卸载 Crabber Skill..."

# 1. Kill running Crabber services
echo "🛑 停止运行中的 Crabber 服务..."
pids=$(ps -ef | grep "venv/bin/uvicorn" | grep -v grep | awk '{print $2}')
if [ -n "$pids" ]; then
    echo "正在终止服务进程: $pids"
    kill $pids || true
fi

# 2. Remove sandbox
echo "🧹 清理沙箱目录 (~/.crabber)..."
rm -rf "$HOME/.crabber"

# 3. Remove Hermes skill if exists
HERMES_SKILL="$HOME/.hermes/skills/crabber.py"
if [ -f "$HERMES_SKILL" ]; then
    echo "🔗 移除 Hermes Skill 插件..."
    rm -f "$HERMES_SKILL"
fi

echo "✅ Crabber 卸载成功！"
echo "=========================================="
echo "提示：如果您曾将 ~/.crabber/bin 添加到了系统环境变量，"
echo "请记得从您的 ~/.zshrc 或 ~/.bash_profile 中移除以下行："
echo "export PATH=\"\$HOME/.crabber/bin:\$PATH\""
echo "=========================================="
echo ""
