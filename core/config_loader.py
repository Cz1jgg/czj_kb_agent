# =========================================
#  配置加载：读取 config/settings.yaml 与 .env
#  对外返回 dict 形式的配置对象
# =========================================
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# 项目根目录（相对于本文件的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 默认配置文件路径
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.yaml"
DEFAULT_PROMPTS_PATH = PROJECT_ROOT / "config" / "prompts.yaml"
ENV_PATH = PROJECT_ROOT / ".env"


def load_settings(settings_path: Path = DEFAULT_SETTINGS_PATH) -> dict:
    """
    加载全局配置：
      1. 加载 .env（若存在）写入环境变量
      2. 读取 settings.yaml
    返回 dict，结构与 settings.yaml 一致。
    """
    # 1) 加载 .env
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

    # 2) 读取 settings.yaml
    with open(settings_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # 补充：把部分环境变量写入配置（便于核心逻辑使用）
    data["_env"] = {
        "DASHSCOPE_API_KEY": os.getenv("DASHSCOPE_API_KEY", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", ""),
        "JAVA_SERVICE_BASE_URL": os.getenv(
            "JAVA_SERVICE_BASE_URL",
            data.get("java_service", {}).get("base_url", ""),
        ),
    }

    data["_project_root"] = str(PROJECT_ROOT)
    return data


def load_prompts(prompts_path: Path = DEFAULT_PROMPTS_PATH) -> dict:
    """加载 prompts.yaml，返回 {qa_template, condense_template}。"""
    with open(prompts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
