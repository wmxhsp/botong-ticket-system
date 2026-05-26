"""
博通 (Botong) — 数据库维护后台任务

这些任务由 RQ Worker 按 cron 调度周期执行。
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def vacuum_database(**kwargs) -> Dict[str, Any]:
    """
    执行完整数据库维护（推荐 cron: 每周日凌晨 3 点）
    
    包括: VACUUM + REINDEX + ANALYZE + WAL checkpoint
    """
    from infrastructure.persistence.maintenance import get_maintenance

    try:
        maint = get_maintenance()
        logger.info("Starting weekly database maintenance...")

        result = maint.full_maintenance()
        size_before = maint.get_db_size()

        # VACUUM 后再次检查大小
        size_after = maint.get_db_size()

        report = {
            **result,
            "size_mb_before": size_before.get("total_mb"),
            "size_mb_after": size_after.get("total_mb"),
            "freed_mb": (size_before.get("total_mb", 0)
                         - size_after.get("total_mb", 0)),
        }
        logger.info("Database maintenance completed: %s", report)
        return {"status": "ok", **report}

    except Exception as e:
        logger.error("Database maintenance failed: %s", e)
        return {"status": "error", "message": str(e)}


def analyze_queries(**kwargs) -> Dict[str, Any]:
    """
    更新数据库查询统计（推荐 cron: 每日凌晨执行）
    
    帮助 SQLite 查询优化器选择最佳索引。
    """
    from infrastructure.persistence.legacy_db import get_db

    try:
        with get_db() as conn:
            conn.execute("ANALYZE")
        logger.info("Query statistics updated (ANALYZE)")
        return {"status": "ok", "action": "analyze"}
    except Exception as e:
        logger.error("ANALYZE failed: %s", e)
        return {"status": "error", "message": str(e)}
