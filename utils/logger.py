# =========================================
#  日志配置：控制台 + 文件双输出
# =========================================
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 默认日志目录（可被外部覆盖）
_DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

_initialized = False


def setup_logger(log_dir: str = None, level=logging.INFO) -> logging.Logger:
    """
    初始化 logger，返回根 logger。
    输出：
      - 控制台（INFO 以上）
      - logs/app.log（轮转，单文件 5MB，保留 5 份）
    """
    global _initialized
    if _initialized:
        return logging.getLogger()

    log_dir = Path(log_dir) if log_dir else _DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger = logging.getLogger()
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件（轮转）
    fh = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    _initialized = True
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """获取命名 logger，若未初始化则先初始化一次。"""
    if not _initialized:
        setup_logger()
    return logging.getLogger(name)
