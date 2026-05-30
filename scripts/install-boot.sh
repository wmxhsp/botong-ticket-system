#!/bin/bash
# ==========================================================
# 博通工单系统 — 开机启动一键安装脚本
# ==========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

cd "$APP_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  博通工单系统 — 开机启动安装"
echo "=========================================="
echo "  目录: $APP_DIR"
echo ""

if [[ "$(uname -s)" == "Darwin" ]]; then
    echo -e "${YELLOW}→  macOS 检测到${NC}"
    echo ""
    
    PLIST_SRC="$SCRIPT_DIR/com.boto.ticket.system.plist"
    PLIST_DEST="$HOME/Library/LaunchAgents/com.boto.ticket.system.plist"
    
    if [ -f "$PLIST_DEST" ]; then
        echo -e "${YELLOW}⚠️  已存在配置，正在卸载...${NC}"
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
        rm -f "$PLIST_DEST"
    fi
    
    cp "$PLIST_SRC" "$PLIST_DEST"
    
    echo -e "${GREEN}✅  配置文件已安装${NC}"
    echo "  $PLIST_DEST"
    echo ""
    
    read -p "  立即启动服务？[y/n] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        launchctl load "$PLIST_DEST"
        sleep 2
        if launchctl list | grep -q com.boto.ticket.system; then
            echo -e "${GREEN}✅  服务已启动${NC}"
            echo "  本地访问: http://localhost:5053"
            echo "  日志: /tmp/boto-system.log"
        else
            echo -e "${RED}❌  服务启动失败${NC}"
            echo "  查看日志: /tmp/boto-system.err"
        fi
    fi
    
    echo ""
    echo "  管理命令:"
    echo "    查看状态: launchctl list | grep boto"
    echo "    启动:     launchctl load $PLIST_DEST"
    echo "    停止:     launchctl unload $PLIST_DEST"
    echo "    重启:     launchctl unload $PLIST_DEST && launchctl load $PLIST_DEST"
    
elif [[ "$(uname -s)" == "Linux" ]]; then
    echo -e "${YELLOW}→  Linux 检测到${NC}"
    echo ""
    
    SERVICE_SRC="$SCRIPT_DIR/botong.service"
    SERVICE_DEST="/etc/systemd/system/botong.service"
    
    if [ -f "$SERVICE_DEST" ]; then
        echo -e "${YELLOW}⚠️  已存在服务，正在卸载...${NC}"
        sudo systemctl stop botong 2>/dev/null || true
        sudo systemctl disable botong 2>/dev/null || true
        sudo rm -f "$SERVICE_DEST"
    fi
    
    sed -e "s|%USER%|$(whoami)|g" \
        -e "s|%APP_DIR%|$APP_DIR|g" \
        "$SERVICE_SRC" | sudo tee "$SERVICE_DEST" >/dev/null
    
    sudo systemctl daemon-reload
    
    echo -e "${GREEN}✅  Systemd 服务已安装${NC}"
    echo "  $SERVICE_DEST"
    echo ""
    
    read -p "  立即启动服务并开机自启？[y/n] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl enable botong
        sudo systemctl start botong
        sleep 2
        if sudo systemctl is-active --quiet botong; then
            echo -e "${GREEN}✅  服务已启动${NC}"
            echo "  本地访问: http://localhost:5053"
            echo "  日志: /tmp/boto-system.log"
        else
            echo -e "${RED}❌  服务启动失败${NC}"
            sudo systemctl status botong -n 20
        fi
    fi
    
    echo ""
    echo "  管理命令:"
    echo "    查看状态: sudo systemctl status botong"
    echo "    启动:     sudo systemctl start botong"
    echo "    停止:     sudo systemctl stop botong"
    echo "    重启:     sudo systemctl restart botong"
    echo "    日志:     sudo journalctl -u botong -f"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅  安装完成${NC}"
echo "=========================================="
