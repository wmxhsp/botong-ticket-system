#!/bin/bash
# 博通工单系统 - Tailscale 状态检查脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=" * 60
echo "🔍 Tailscale 状态检查"
echo "=" * 60

# 检查 Tailscale 是否安装
if command -v tailscale &>/dev/null; then
    echo "✅ Tailscale 已安装"
    echo ""
    echo "=== Tailscale 状态 ==="
    tailscale status 2>/dev/null || echo "⚠️  Tailscale 可能未运行"
    
    echo ""
    echo "=== 当前 IP ==="
    tailscale ip 2>/dev/null || echo "⚠️  无法获取 Tailscale IP"
    
    echo ""
    echo "=== 主机名 ==="
    TAILSCALE_HOST=$(tailscale status --json 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('Self', {}).get('DNSName', ''))" 2>/dev/null || "")
    if [ -n "$TAILSCALE_HOST" ]; then
        echo "✅ $TAILSCALE_HOST"
        echo ""
        echo "建议在 .env 中设置："
        echo "BOTO_TAILSCALE_HOST=$TAILSCALE_HOST"
        echo "BOTO_HOST=0.0.0.0"
    else
        echo "⚠️  无法获取 Tailscale 主机名"
    fi
else
    echo "❌ Tailscale 未安装或不在 PATH 中"
    echo ""
    echo "安装指引："
    echo "  macOS: brew install tailscale"
    echo "  Linux: curl -fsSL https://tailscale.com/install.sh | sh"
    echo "  其他: https://tailscale.com/download"
fi

echo ""
echo "=" * 60
