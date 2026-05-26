#!/bin/bash
# ==================================================
# 博通 (Botong) — 启动/停止/备份脚本
# 用法:
#   ./scripts/manage.sh start      启动服务
#   ./scripts/manage.sh stop       停止服务
#   ./scripts/manage.sh restart    重启服务
#   ./scripts/manage.sh backup     备份数据库
#   ./scripts/manage.sh status     查看状态
#   ./scripts/manage.sh test       运行测试
# ==================================================

cd "$(dirname "$0")/.."
APP_DIR=$(pwd)
DB_FILE="$APP_DIR/tickets.db"
BACKUP_DIR="$APP_DIR/backups"
PID_FILE="/tmp/boto-app.pid"
LOG_FILE="/tmp/boto-app.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$BACKUP_DIR"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  服务已在运行中 (PID: $(cat $PID_FILE))${NC}"
        return
    fi
    echo -e "${GREEN}🚀 启动博通...${NC}"
    cd "$APP_DIR"
    nohup /usr/bin/python3 app.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo -e "${GREEN}✅ 服务已启动 (PID: $(cat $PID_FILE))${NC}"
        echo -e "   本地: ${GREEN}http://localhost:5050${NC}"
        echo -e "   日志: ${GREEN}$LOG_FILE${NC}"
    else
        echo -e "${RED}❌ 启动失败，查看日志: $LOG_FILE${NC}"
    fi
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}⚠️  未找到 PID 文件${NC}"
        pkill -f "python3 app.py" 2>/dev/null && echo -e "${GREEN}✅ 已停止${NC}" || echo -e "${YELLOW}无运行中的服务${NC}"
        return
    fi
    PID=$(cat "$PID_FILE")
    echo -e "⏹️  停止服务 (PID: $PID)..."
    kill "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    sleep 1
    echo -e "${GREEN}✅ 已停止${NC}"
}

backup() {
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/tickets_$TIMESTAMP.db"
    echo -e "💾 备份数据库..."
    # 使用 WAL checkpoint 确保数据一致性
    sqlite3 "$DB_FILE" "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null
    cp "$DB_FILE" "$BACKUP_FILE"
    # 压缩备份
    gzip -f "$BACKUP_FILE" 2>/dev/null
    echo -e "${GREEN}✅ 备份完成: ${BACKUP_FILE}.gz${NC}"
    # 保留最近30天，删除旧备份
    find "$BACKUP_DIR" -name "tickets_*.db.gz" -mtime +30 -delete 2>/dev/null
    echo -e "   已保留 $(ls $BACKUP_DIR/*.db.gz 2>/dev/null | wc -l) 个备份"
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ 服务运行中${NC}"
        echo -e "   PID: $PID"
        echo -e "   端口: 5050"
        echo -e "   运行时间: $(ps -o etime= -p $PID | tr -d ' ')"
    else
        echo -e "${YELLOW}⏹️  服务未运行${NC}"
    fi
    echo -e "   数据库: $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"
    echo -e "   备份:   $(ls $BACKUP_DIR/*.db.gz 2>/dev/null | wc -l) 个"
}

run_tests() {
    echo -e "${GREEN}🧪 运行测试...${NC}"
    BOTO_NO_RATE_LIMIT=1 /usr/bin/python3 -m pytest tests/ -v
}

# ==================================================

case "${1:-status}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 1; start ;;
    backup)  backup ;;
    status)  status ;;
    test)    run_tests ;;
    *)
        echo "用法: $0 {start|stop|restart|backup|status|test}"
        exit 1
        ;;
esac
