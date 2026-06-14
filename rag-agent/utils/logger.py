"""
日志基础配置：同时输出到控制台与 logs/rag-agent.log
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from utils.file_utils import ensure_dir, abs_path

_LOGGER_INITED = False


def setup_logger(name: str = "rag-agent", log_level: int = logging.INFO) -> logging.Logger:
    """初始化并返回全局 logger（幂等）。"""
    global _LOGGER_INITED

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if _LOGGER_INITED:
        return logger

    log_dir = abs_path("logs")
    ensure_dir(log_dir)
    log_path = os.path.join(log_dir, f"{name}.log")

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console = logging.StreamHandler()
    console.setLevel(log_level)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # 文件输出：按大小轮转，保留 5 份，单份 5MB
    file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.propagate = False
    _LOGGER_INITED = True
    return logger


# 便捷入口
logger = setup_logger()
