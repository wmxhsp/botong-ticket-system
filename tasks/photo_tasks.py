"""
博通 (Botong) — 照片处理后台任务（打水印、保存记录）

任务函数供 RQ Worker 或 LocalTaskQueue 调用。
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def process_watermark(raw_path: str, ticket_id: int, filename: str) -> Dict[str, Any]:
    """异步打水印并保存照片记录。

    Args:
        raw_path: 上传的原始文件路径（带 raw_ 前缀）
        ticket_id: 工单 ID
        filename: 目标文件名（例如 wm_...jpg）

    Returns:
        dict: 执行结果状态
    """
    try:
        # 延迟导入以避免启动时循环依赖
        from infrastructure.di.container import Container
        ticket_svc = Container.resolve("ticket_service")

        # 执行水印操作（TicketService 提供的封装）
        try:
            ticket_svc.add_watermark(raw_path, ticket_id)
        except Exception as e:
            logger.error("process_watermark: add_watermark failed: %s", e)
            # 继续尝试保存（如果有部分产物）

        # 保存照片记录到 DB
        filepath = f"static/uploads/tickets/{ticket_id}/{filename}"
        try:
            ticket_svc.save_photo(ticket_id, filename, filepath)
        except Exception as e:
            logger.error("process_watermark: save_photo failed: %s", e)
            return {"status": "error", "message": str(e)}

        # 可选：删除原始 raw 文件以节省空间
        try:
            import os
            if os.path.exists(raw_path):
                os.remove(raw_path)
        except Exception:
            pass

        logger.info("process_watermark: finished for ticket %s -> %s", ticket_id, filename)
        # 更新状态文件（附加一条 finished 记录）
        try:
            import os, json
            os.makedirs(os.path.join(os.getcwd(), '.data'), exist_ok=True)
            status_path = os.path.join(os.getcwd(), '.data', 'photo_task_status.json')
            with open(status_path, 'a', encoding='utf-8') as sf:
                sf.write(json.dumps({
                    'task_id': None,
                    'ticket_id': ticket_id,
                    'filename': filename,
                    'status': 'finished',
                    'finished_at': datetime.now().isoformat(),
                    'filepath': filepath,
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass

        return {"status": "ok", "filepath": filepath}

    except Exception as e:
        logger.exception("process_watermark unexpected error: %s", e)
        try:
            import os, json
            os.makedirs(os.path.join(os.getcwd(), '.data'), exist_ok=True)
            status_path = os.path.join(os.getcwd(), '.data', 'photo_task_status.json')
            with open(status_path, 'a', encoding='utf-8') as sf:
                sf.write(json.dumps({
                    'task_id': None,
                    'ticket_id': ticket_id,
                    'filename': filename,
                    'status': 'failed',
                    'message': str(e),
                    'time': datetime.now().isoformat(),
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return {"status": "error", "message": str(e)}
