#!/bin/bash
# ==================================================
# 自动安装脚本 — 初始化备份 cron 和服务自启
# 用法: bash scripts/setup.sh
# ==================================================

cd "$(dirname "$0")/.."
APP_DIR=$(pwd)
SCRIPT="$APP_DIR/scripts/manage.sh"

echo "============================================"
echo "  博通 (Botong) — 环境初始化"
echo "============================================"

# 1. 检查数据库
echo -n "📂 检查数据库... "
if [ -f "$APP_DIR/tickets.db" ]; then
    SIZE=$(du -h "$APP_DIR/tickets.db" | cut -f1)
    echo "✅ ($SIZE)"
else
    echo "❌ 未找到 tickets.db"
    exit 1
fi

# 2. 创建备份目录
mkdir -p "$APP_DIR/backups"
echo "📁 备份目录: $APP_DIR/backups"

# 3. 设置每日 02:00 自动备份
CRON_JOB="0 2 * * * cd $APP_DIR && $SCRIPT backup >> $APP_DIR/backups/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "$SCRIPT"; echo "$CRON_JOB") | crontab -
echo "⏰ 已设置每日 02:00 自动备份 (crontab)"

# 4. 设置每小时备份（仅保留最近7天，用于快速恢复）
CRON_HOURLY="0 * * * * cd $APP_DIR && sqlite3 tickets.db \".backup backups/tickets_hourly.db\" && find backups -name 'tickets_hourly.db' -mtime +7 -delete > /dev/null 2>&1"
(crontab -l 2>/dev/null | grep -v "tickets_hourly"; echo "$CRON_HOURLY") | crontab -
echo "⏰ 已设置每小时快速备份 (保留7天)"

# 5. 设置自动启动 (macOS LaunchAgent)
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.boto.ticket.plist"
mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.boto.ticket</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${APP_DIR}/app.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${APP_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/boto-app.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/boto-app.log</string>
</dict>
</plist>
EOF

# 加载 LaunchAgent（登录时自启）
launchctl load "$PLIST_FILE" 2>/dev/null
echo "🚀 已设置登录时自启 (LaunchAgent)"

echo ""
echo "============================================"
echo "  ✅ 初始化完成！"
echo "============================================"
echo "  每日备份:  02:00 (保留30天)"
echo "  每小时备份: 保留7天"
echo "  自启:      登录时自动启动"
echo ""
echo "  手动命令:"
echo "    ./scripts/manage.sh start    启动"
echo "    ./scripts/manage.sh stop     停止"
echo "    ./scripts/manage.sh backup   立即备份"
echo "    ./scripts/manage.sh status   查看状态"
echo "============================================"
