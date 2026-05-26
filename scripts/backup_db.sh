#!/bin/bash
# ================================================
# 博通 (Botong) — 数据库自动备份脚本
# 用途：每日备份 tickets.db，保留最近 30 天备份
# 用法：./scripts/backup_db.sh
# 可配合 crontab 自动执行:
#   0 2 * * * /path/to/scripts/backup_db.sh
# ================================================

set -euo pipefail

# 配置
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_PATH="${BASE_DIR}/tickets.db"
BACKUP_DIR="${BASE_DIR}/backups"
RETENTION_DAYS=30
DATE_STAMP=$(date "+%Y%m%d_%H%M%S")
BACKUP_PATH="${BACKUP_DIR}/tickets_${DATE_STAMP}.db"
LOG_FILE="${BACKUP_DIR}/backup.log"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 检查数据库是否存在
if [ ! -f "${DB_PATH}" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Database not found at ${DB_PATH}" >> "${LOG_FILE}"
    exit 1
fi

# 执行备份（使用 SQLite 在线备份确保一致性）
sqlite3 "${DB_PATH}" ".backup '${BACKUP_PATH}'"

# 索引维护（ANALYZE + REINDEX 保持查询性能）
sqlite3 "${DB_PATH}" "ANALYZE"
sqlite3 "${DB_PATH}" "REINDEX"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Index maintenance completed" >> "${LOG_FILE}"

# 验证备份
if [ -f "${BACKUP_PATH}" ]; then
    BACKUP_SIZE=$(stat -f%z "${BACKUP_PATH}" 2>/dev/null || stat -c%s "${BACKUP_PATH}" 2>/dev/null)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] OK: Backed up to ${BACKUP_PATH} (${BACKUP_SIZE} bytes)" >> "${LOG_FILE}"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Backup file not created" >> "${LOG_FILE}"
    exit 1
fi

# 清理旧备份（保留最近 RETENTION_DAYS 天）
find "${BACKUP_DIR}" -name "tickets_*.db" -type f -mtime +${RETENTION_DAYS} -delete

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleanup: removed backups older than ${RETENTION_DAYS} days" >> "${LOG_FILE}"
echo "Backup complete: ${BACKUP_PATH}"
