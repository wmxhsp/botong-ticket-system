"""
博通 (Botong) — 数据库定期维护调度

用法：
  python -m infrastructure.persistence.db_maintenance           # 执行一次
  python -m infrastructure.persistence.db_maintenance --weekly   # 每周模式（含 VACUUM）
"""
import sys
import logging

logger = logging.getLogger(__name__)


def run_daily():
    """每日维护：清理缓存 + 审计归档 + ANALYZE + WAL checkpoint"""
    from infrastructure.persistence.legacy_db import run_maintenance
    logger.info("开始每日数据库维护...")
    run_maintenance()
    logger.info("每日数据库维护完成")


def run_weekly():
    """每周维护：每日 + VACUUM"""
    from infrastructure.persistence.legacy_db import run_maintenance, maintain_vacuum
    logger.info("开始每周数据库维护...")
    run_maintenance()
    maintain_vacuum()
    logger.info("每周数据库维护完成")


def run_backup(db_path: str = None, backup_dir: str = None):
    """
    热备份数据库文件
    使用 sqlite3 .backup 命令，WAL 模式下安全可用
    
    Args:
        db_path: 数据库文件路径，默认自动检测
        backup_dir: 备份目录，默认为数据库同目录下的 backups/
    """
    import os
    import sqlite3
    from datetime import datetime
    
    if db_path is None:
        from infrastructure.persistence.legacy_db import DB_FILE
        db_path = DB_FILE
    
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"botong_{timestamp}.db")
    
    try:
        source = sqlite3.connect(db_path)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        dest.close()
        source.close()
        
        # 保留最近30天备份，删除更早的
        _cleanup_old_backups(backup_dir, keep_days=30)
        
        size_mb = os.path.getsize(backup_path) / 1024 / 1024
        logger.info(f"数据库备份完成: {backup_path} ({size_mb:.1f}MB)")
        return backup_path
    except Exception as e:
        logger.error(f"数据库备份失败: {e}")
        raise


def _cleanup_old_backups(backup_dir: str, keep_days: int = 30):
    """清理过期备份文件"""
    import os
    import time
    
    cutoff = time.time() - keep_days * 86400
    for f in os.listdir(backup_dir):
        fp = os.path.join(backup_dir, f)
        if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
            try:
                os.remove(fp)
                logger.info(f"删除过期备份: {f}")
            except OSError:
                pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    if "--weekly" in sys.argv:
        run_weekly()
    elif "--backup" in sys.argv:
        run_backup()
    else:
        run_daily()
