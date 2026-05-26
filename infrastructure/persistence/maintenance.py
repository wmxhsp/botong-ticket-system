"""
博通 — 数据库维护工具
VACUUM / 索引分析 / 性能诊断 / WAL 管理
"""

import logging
import os
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseMaintenance:
    """数据库维护"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            from infrastructure.persistence.legacy_db import DB_FILE
            db_path = DB_FILE
        self.db_path = db_path

    def get_db_size(self) -> dict:
        """获取数据库文件尺寸"""
        path = Path(self.db_path)
        sizes = {}
        for suffix in ["", "-wal", "-shm"]:
            f = path.parent / (path.name + suffix)
            if f.exists():
                sizes[f.name] = round(f.stat().st_size / 1024, 1)
        sizes["total_kb"] = sum(sizes.values())
        sizes["total_mb"] = round(sizes["total_kb"] / 1024, 2)
        return sizes

    def get_pragma_info(self) -> dict:
        """获取数据库 PRAGMA 信息（页面数、页面大小、日志模式）"""
        try:
            from infrastructure.persistence.legacy_db import get_db
            with get_db() as conn:
                page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                wal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            return {
                "page_count": page_count,
                "page_size": page_size,
                "journal_mode": wal_mode,
            }
        except Exception:
            return {
                "page_count": 0,
                "page_size": 4096,
                "journal_mode": "unknown",
            }

    def vacuum(self) -> dict:
        """执行 VACUUM 收缩数据库"""
        from infrastructure.persistence.legacy_db import get_db
        start = time.time()
        try:
            with get_db() as conn:
                conn.execute("VACUUM")
            elapsed = round(time.time() - start, 2)
            size_after = self.get_db_size()
            logger.info(f"VACUUM 完成: {elapsed}s, 当前 {size_after['total_mb']}MB")
            return {"success": True, "elapsed_seconds": elapsed, **size_after}
        except Exception as e:
            logger.error(f"VACUUM 失败: {e}")
            return {"success": False, "error": str(e)}

    def reindex(self) -> dict:
        """重建所有索引"""
        from infrastructure.persistence.legacy_db import get_db
        start = time.time()
        try:
            with get_db() as conn:
                conn.execute("REINDEX")
            elapsed = round(time.time() - start, 2)
            logger.info(f"REINDEX 完成: {elapsed}s")
            return {"success": True, "elapsed_seconds": elapsed}
        except Exception as e:
            logger.error(f"REINDEX 失败: {e}")
            return {"success": False, "error": str(e)}

    def analyze(self) -> dict:
        """分析查询计划"""
        from infrastructure.persistence.legacy_db import get_db, db_query
        start = time.time()
        try:
            with get_db() as conn:
                conn.execute("ANALYZE")
            elapsed = round(time.time() - start, 2)

            # 获取表统计信息
            tables = db_query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            table_stats = []
            for t in tables:
                count = db_query(
                    f"SELECT COUNT(*) as cnt FROM \"{t['name']}\"")
                table_stats.append({
                    "name": t["name"],
                    "rows": count[0]["cnt"] if count else 0,
                })

            # 获取数据库页面信息
            db_info = {"page_size": 4096}
            with get_db() as conn:
                info = conn.execute("PRAGMA page_count").fetchone()
                db_info["page_count"] = info[0] if info else 0
                info = conn.execute("PRAGMA page_size").fetchone()
                db_info["page_size"] = info[0] if info else 4096
                db_info["total_pages"] = db_info["page_count"]
                db_info["total_size_mb"] = round(
                    db_info["page_count"] * db_info["page_size"] / 1024 / 1024, 2)

            return {
                "success": True,
                "elapsed_seconds": elapsed,
                "table_stats": table_stats,
                "db_info": db_info,
            }
        except Exception as e:
            logger.error(f"ANALYZE 失败: {e}")
            return {"success": False, "error": str(e)}

    def wal_checkpoint(self) -> dict:
        """强制 WAL checkpoint"""
        from infrastructure.persistence.legacy_db import get_db
        try:
            with get_db() as conn:
                before = self.get_db_size()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                after = self.get_db_size()
            return {
                "success": True,
                "wal_before_kb": before.get(f"{Path(self.db_path).name}-wal", 0),
                "wal_after_kb": after.get(f"{Path(self.db_path).name}-wal", 0),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def full_maintenance(self) -> dict:
        """完整维护流程"""
        results = {}
        results["analyze"] = self.analyze()
        results["wal_checkpoint"] = self.wal_checkpoint()
        results["reindex"] = self.reindex()
        results["vacuum"] = self.vacuum()
        results["size"] = self.get_db_size()
        return results

    def schedule_daily(self):
        """启动每日定时维护（在后台线程运行）"""
        def _maintenance_loop():
            logger.info("数据库维护线程已启动（每24小时执行一次）")
            while True:
                try:
                    time.sleep(86400)  # 24 小时
                    logger.info("开始每日数据库维护...")
                    self.full_maintenance()
                    logger.info("每日数据库维护完成")
                except Exception as e:
                    logger.error(f"每日维护异常: {e}")

        t = threading.Thread(target=_maintenance_loop, daemon=True)
        t.start()
        return t


# 全局实例
_maintenance = None


def get_maintenance() -> DatabaseMaintenance:
    """获取维护实例"""
    global _maintenance
    if _maintenance is None:
        _maintenance = DatabaseMaintenance()
    return _maintenance
