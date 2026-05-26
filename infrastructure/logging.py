"""
博通 (Botong) — 结构化日志配置
统一日志格式，支持 JSON 输出和上下文绑定
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any


class StructuredFormatter(logging.Formatter):
    """结构化 JSON 日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 合并 extra 字段
        for key, value in getattr(record, "extra", {}).items():
            log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_output: bool = False):
    """
    初始化日志系统
    
    Args:
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        json_output: True=JSON格式, False=控制台友好格式
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # 清除已有 handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    if json_output:
        console.setFormatter(StructuredFormatter())
    else:
        console.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
    root_logger.addHandler(console)
    
    # 文件 handler（按天滚动）
    try:
        from logging.handlers import TimedRotatingFileHandler
        file_handler = TimedRotatingFileHandler(
            "/tmp/botong-app.log",
            when="midnight",
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
        ))
        root_logger.addHandler(file_handler)
    except Exception:
        pass
    
    return root_logger


def get_logger(name: str):
    """获取日志器"""
    return logging.getLogger(name)
