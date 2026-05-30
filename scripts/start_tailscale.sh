#!/bin/bash
# 博通工单系统 - Tailscale 模式启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# 检查是否有 Tailscale 相关配置
TAILSCALE_CONFIG="$PROJECT_ROOT/config/tailscale.json"
if [ -f "$TAILSCALE_CONFIG" ]; then
    echo "📋 检测到 Tailscale 配置文件"
    TAILSCALE_HOST=$(python3 -c "import json; print(json.load(open('$TAILSCALE_CONFIG')).get('tailscale_host', ''))" 2>/dev/null || "")
    if [ -n "$TAILSCALE_HOST" ]; then
        export BOTO_TAILSCALE_HOST="$TAILSCALE_HOST"
        echo "🔗 Tailscale 主机名: $TAILSCALE_HOST"
    fi
fi

# 默认启用 Tailscale 访问
export BOTO_HOST="${BOTO_HOST:-0.0.0.0}"
export BOTO_PORT="${BOTO_PORT:-5053}"

echo "=" * 60
echo "🚀 启动博通工单系统 (Tailscale 模式)"
echo "=" * 60
echo "📂 项目目录: $PROJECT_ROOT"
echo "🌐 绑定地址: $BOTO_HOST"
echo "🔌 端口: $BOTO_PORT"
if [ -n "$BOTO_TAILSCALE_HOST" ]; then
    echo "🔗 Tailscale 访问: http://$BOTO_TAILSCALE_HOST:$BOTO_PORT"
fi
echo "=" * 60

# 启动应用
if command -v python3 &>/dev/null; then
    python3 app.py
elif command -v python &>/dev/null; then
    python app.py
else
    echo "❌ 未找到 Python，请先安装 Python"
    exit 1
fi
