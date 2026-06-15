# =========================================
#  配置加载模块：读取 settings.yaml + .env，封装为统一配置对象
#
#  使用方式（其他模块直接导入）：
#      from core.config_loader import settings
#      print(settings.server.port)          # 8000
#      print(settings.llm.api_key)           # 从 .env 读取
#      print(settings.upload.allow_extensions) # [".pdf", ".docx", ...]
#
#  优先级：.env > 系统环境变量 > settings.yaml > 代码内置默认值
# =========================================
from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover
    raise ImportError(
        "未安装 PyYAML，请先执行：pip install pyyaml"
    )

try:
    from dotenv import load_dotenv  # python-dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore

# ------------------------------------------------------------
# 路径常量：以本文件位置推导项目根目录，保证在任何工作目录下运行都可找到
# ------------------------------------------------------------
# 本文件所在目录的上一级 = 项目根目录（czj_kb_agent/）
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# 默认配置文件路径
DEFAULT_SETTINGS_PATH: Path = PROJECT_ROOT / "config" / "settings.yaml"
DEFAULT_PROMPTS_PATH: Path = PROJECT_ROOT / "config" / "prompts.yaml"
ENV_PATH: Path = PROJECT_ROOT / ".env"
ENV_EXAMPLE_PATH: Path = PROJECT_ROOT / ".env.example"

# 日志输出（模块级别）
_logger = logging.getLogger(__name__)


# ============================================================
# 异常类：配置加载失败时抛出，便于上层捕获给出友好提示
# ============================================================
class ConfigError(Exception):
    """配置加载/解析错误统一异常类。"""
    pass


# ============================================================
# 工具函数
# ============================================================
def _to_abs_path(p: str) -> str:
    """把相对路径转换为相对于 PROJECT_ROOT 的绝对路径；绝对路径原样返回。"""
    path = Path(p)
    if path.is_absolute():
        return str(path)
    return str((PROJECT_ROOT / path).resolve())


def _ensure_dir(p: str) -> str:
    """确保目录存在，不存在则创建。返回其绝对路径。"""
    abs_path = _to_abs_path(p)
    Path(abs_path).mkdir(parents=True, exist_ok=True)
    return abs_path


def _get_env(key: str, default: Any = "", example_path: Path = ENV_EXAMPLE_PATH) -> str:
    """从环境变量读取值，优先 .env -> 系统环境变量；示例文件 .env.example 只做提示。"""
    value = os.getenv(key, "").strip()
    if value:
        return value
    return str(default) if default is not None else ""


def _load_env_files() -> None:
    """加载 .env 文件；若缺失则给出提示。"""
    if load_dotenv is None:
        _logger.warning("未安装 python-dotenv，跳过 .env 加载；请执行 pip install python-dotenv")
        return

    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
        _logger.info("已加载环境变量文件：%s", ENV_PATH)
    else:
        _logger.warning(
            "未找到 .env 文件（%s），将使用系统环境变量 + settings.yaml 默认值。"
            "可复制 .env.example 为 .env 并填入真实值。",
            ENV_PATH,
        )


# ============================================================
# dataclass 配置分区（便于 IDE 自动补全 & 类型提示）
# ============================================================
@dataclass
class ServerConfig:
    """服务配置：host、port、日志级别。"""
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        # 允许通过 .env 的 SERVER_PORT 覆盖
        env_port = os.getenv("SERVER_PORT", "").strip()
        if env_port:
            try:
                self.port = int(env_port)
            except ValueError:
                raise ConfigError(f"SERVER_PORT='{env_port}' 无法转换为整数，请检查 .env")

        env_log = os.getenv("LOG_LEVEL", "").strip().upper()
        if env_log and env_log in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            self.log_level = env_log


@dataclass
class LLMConfig:
    """LLM 模型配置。"""
    provider: str = "openai"
    model: str = "doubao-lite-128k"
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"  # 火山方舟 OpenAI 兼容接口
    temperature: float = 0.1
    max_tokens: int = 8192
    timeout: int = 60
    # API Key：从 .env 读取，不在 YAML 中硬编码
    api_key: str = ""

    def __post_init__(self) -> None:
        # 用 .env 覆盖默认值
        if os.getenv("LLM_MODEL", "").strip():
            self.model = os.getenv("LLM_MODEL", "").strip()
        if os.getenv("LLM_TEMPERATURE", "").strip():
            try:
                self.temperature = float(os.getenv("LLM_TEMPERATURE", "").strip())
            except ValueError:
                raise ConfigError("LLM_TEMPERATURE 必须是数字（0.0 ~ 2.0）")
        if os.getenv("OPENAI_BASE_URL", "").strip():
            self.base_url = os.getenv("OPENAI_BASE_URL", "").strip()

        # 读取 API Key：火山方舟 ARK > OpenAI API Key
        self.api_key = os.getenv("ARK_API_KEY", "").strip()
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            _logger.warning(
                "⚠️  未配置 LLM API Key（ARK_API_KEY 或 OPENAI_API_KEY 均为空）。"
                "问答功能将无法使用，请在 .env 中填写。"
            )


@dataclass
class EmbeddingConfig:
    """向量 Embedding 模型配置。"""
    provider: str = "dashscope"
    model: str = "text-embedding-v2"
    batch_size: int = 16
    timeout: int = 30
    api_key: str = ""

    def __post_init__(self) -> None:
        if os.getenv("EMBEDDING_MODEL", "").strip():
            self.model = os.getenv("EMBEDDING_MODEL", "").strip()
        # Embedding API Key：火山方舟 ARK > OpenAI
        self.api_key = os.getenv("ARK_API_KEY", "").strip() or os.getenv(
            "OPENAI_API_KEY", ""
        ).strip()


@dataclass
class SplitterConfig:
    """文本分块参数。"""
    chunk_size: int = 500
    chunk_overlap: int = 50
    separator: str = "\n"

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ConfigError("splitter.chunk_size 必须大于 0")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ConfigError(
                "splitter.chunk_overlap 必须满足 0 <= overlap < chunk_size"
            )


@dataclass
class VectorStoreConfig:
    """FAISS 向量库配置。"""
    type: str = "faiss"
    path: str = "data/vector_store"      # 相对路径（相对于 PROJECT_ROOT）
    top_k: int = 4
    score_threshold: float = 0.0

    def __post_init__(self) -> None:
        # 转换为绝对路径并确保目录存在
        self.path = _ensure_dir(self.path)


@dataclass
class UploadConfig:
    """文件上传配置。"""
    save_dir: str = "data/documents"
    parsed_dir: str = "data/parsed"
    max_file_size_mb: int = 50
    allow_extensions: List[str] = field(default_factory=lambda: [".pdf", ".docx", ".doc", ".md", ".txt", ".markdown"])

    def __post_init__(self) -> None:
        self.save_dir = _ensure_dir(self.save_dir)
        self.parsed_dir = _ensure_dir(self.parsed_dir)
        # 统一为小写
        self.allow_extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in (self.allow_extensions or [])
        ]


@dataclass
class PathsConfig:
    """路径总览（与各模块字段保持一致，便于一次性导出）。"""
    documents: str = "data/documents"
    parsed: str = "data/parsed"
    vector_store: str = "data/vector_store"
    logs: str = "logs"

    def __post_init__(self) -> None:
        self.documents = _ensure_dir(self.documents)
        self.parsed = _ensure_dir(self.parsed)
        self.vector_store = _ensure_dir(self.vector_store)
        self.logs = _ensure_dir(self.logs)


@dataclass
class JavaServiceConfig:
    """Java 服务对接（需要主动回写 Java 时使用）。"""
    base_url: str = "http://127.0.0.1:9000"
    timeout: int = 10
    callback_path: str = "/api/kb/callback/qa"

    def __post_init__(self) -> None:
        env_url = os.getenv("JAVA_SERVICE_BASE_URL", "").strip()
        if env_url:
            self.base_url = env_url


# ============================================================
# 统一配置对象
# ============================================================
@dataclass
class Settings:
    """全局配置对象，所有模块通过它读取配置。"""

    server: ServerConfig = field(default_factory=ServerConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embeddings: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    splitter: SplitterConfig = field(default_factory=SplitterConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    java_service: JavaServiceConfig = field(default_factory=JavaServiceConfig)

    # 元信息
    project_root: str = ""
    env: Dict[str, str] = field(default_factory=dict)

    # ---------- 便捷方法 ----------
    def as_dict(self) -> Dict[str, Any]:
        """序列化为 dict，便于调试打印或给 API 使用。"""
        import dataclasses as _dc
        return _dc.asdict(self)

    def summary(self) -> str:
        """输出配置摘要（用于启动日志打印）。"""
        lines = [
            "====== 配置摘要 ======",
            f"项目根目录: {self.project_root}",
            f"服务        : http://{self.server.host}:{self.server.port}",
            f"日志级别    : {self.server.log_level}",
            f"LLM         : {self.llm.provider} / {self.llm.model} @ {self.llm.base_url} (api_key={'已配置' if self.llm.api_key else '未配置'})",
            f"Embedding   : {self.embeddings.provider} / {self.embeddings.model}",
            f"分块参数    : chunk_size={self.splitter.chunk_size}, overlap={self.splitter.chunk_overlap}",
            f"FAISS 路径  : {self.vector_store.path}",
            f"文档目录    : {self.upload.save_dir}",
            f"支持格式    : {', '.join(self.upload.allow_extensions)}",
            f"Java 服务   : {self.java_service.base_url}",
            "========================",
        ]
        return "\n".join(lines)


# ============================================================
# 配置解析与构造
# ============================================================
def _load_yaml(path: Path) -> Dict[str, Any]:
    """读取 YAML 文件，不存在 / 格式错误会给出友好提示。"""
    if not path.exists():
        raise ConfigError(
            f"❌ 找不到配置文件：{path}\n"
            f"   请确认路径是否正确，或从仓库恢复该文件。"
        )
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigError(
            f"❌ 解析 YAML 失败：{path}\n"
            f"   语法错误详情：{exc}\n"
            f"   请检查缩进（YAML 必须使用 2 空格）。"
        ) from exc
    return data or {}


def _pick(d: Dict[str, Any], key: str, default: Any = None) -> Any:
    """安全地取 dict 字段，缺失时返回默认值并记录警告。"""
    if not isinstance(d, dict):
        return default
    value = d.get(key, None)
    if value is None:
        return default
    return value


def build_settings(settings_path: Path = DEFAULT_SETTINGS_PATH) -> Settings:
    """
    构造 Settings 对象：
      1. 加载 .env 到 os.environ
      2. 读取 settings.yaml
      3. 按分区填入各 dataclass
    """
    # 1. 环境变量
    _load_env_files()

    # 2. settings.yaml
    yaml_root = _load_yaml(settings_path)

    # 3. 按分区构造
    server_yaml = yaml_root.get("server") or {}
    llm_yaml = yaml_root.get("llm") or {}
    emb_yaml = yaml_root.get("embeddings") or {}
    split_yaml = yaml_root.get("splitter") or {}
    vs_yaml = yaml_root.get("vector_store") or {}
    up_yaml = yaml_root.get("upload") or {}
    paths_yaml = yaml_root.get("paths") or {}
    java_yaml = yaml_root.get("java_service") or {}

    settings = Settings(
        server=ServerConfig(
            host=_pick(server_yaml, "host", "0.0.0.0"),
            port=int(_pick(server_yaml, "port", 8000)),
            log_level=_pick(server_yaml, "log_level", "INFO"),
        ),
        llm=LLMConfig(
            provider=_pick(llm_yaml, "provider", "openai"),
            model=_pick(llm_yaml, "model", "doubao-lite-128k"),
            base_url=_pick(llm_yaml, "base_url", "https://ark.cn-beijing.volces.com/api/v3"),
            temperature=float(_pick(llm_yaml, "temperature", 0.1)),
            max_tokens=int(_pick(llm_yaml, "max_tokens", 8192)),
            timeout=int(_pick(llm_yaml, "timeout", 60)),
        ),
        embeddings=EmbeddingConfig(
            provider=_pick(emb_yaml, "provider", "dashscope"),
            model=_pick(emb_yaml, "model", "text-embedding-v2"),
            batch_size=int(_pick(emb_yaml, "batch_size", 16)),
            timeout=int(_pick(emb_yaml, "timeout", 30)),
        ),
        splitter=SplitterConfig(
            chunk_size=int(_pick(split_yaml, "chunk_size", 500)),
            chunk_overlap=int(_pick(split_yaml, "chunk_overlap", 50)),
            separator=_pick(split_yaml, "separator", "\n"),
        ),
        vector_store=VectorStoreConfig(
            type=_pick(vs_yaml, "type", "faiss"),
            path=_pick(vs_yaml, "path", "data/vector_store"),
            top_k=int(_pick(vs_yaml, "top_k", 4)),
            score_threshold=float(_pick(vs_yaml, "score_threshold", 0.0)),
        ),
        upload=UploadConfig(
            save_dir=_pick(up_yaml, "save_dir", "data/documents"),
            parsed_dir=_pick(up_yaml, "parsed_dir", "data/parsed"),
            max_file_size_mb=int(_pick(up_yaml, "max_file_size_mb", 50)),
            allow_extensions=_pick(
                up_yaml, "allow_extensions",
                [".pdf", ".docx", ".doc", ".md", ".txt", ".markdown"],
            ),
        ),
        paths=PathsConfig(
            documents=_pick(paths_yaml, "documents", "data/documents"),
            parsed=_pick(paths_yaml, "parsed", "data/parsed"),
            vector_store=_pick(paths_yaml, "vector_store", "data/vector_store"),
            logs=_pick(paths_yaml, "logs", "logs"),
        ),
        java_service=JavaServiceConfig(
            base_url=_pick(java_yaml, "base_url", "http://127.0.0.1:9000"),
            timeout=int(_pick(java_yaml, "timeout", 10)),
            callback_path=_pick(java_yaml, "callback_path", "/api/kb/callback/qa"),
        ),
        project_root=str(PROJECT_ROOT),
        env={
            "ARK_API_KEY": os.getenv("ARK_API_KEY", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
            "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", ""),
            "JAVA_SERVICE_BASE_URL": os.getenv("JAVA_SERVICE_BASE_URL", ""),
        },
    )

    _logger.info("配置加载完成：%s", settings_path)
    return settings


def load_prompts(prompts_path: Path = DEFAULT_PROMPTS_PATH) -> Dict[str, str]:
    """加载 prompts.yaml，返回 {qa_template, condense_template}。"""
    data = _load_yaml(prompts_path)
    return {
        "qa_template": _pick(data, "qa_template", ""),
        "condense_template": _pick(data, "condense_template", ""),
    }


# ============================================================
# 全局单例：其他模块直接 `from core.config_loader import settings`
# ============================================================
# _loaded_env_mtime: 记录上次加载时的 .env 文件修改时间，用于检测变更
_loaded_env_mtime: Optional[float] = None
_settings: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """
    获取全局配置单例。

    - reload=True 时强制重新加载（用于调试修改了 settings.yaml 的情况）
    - .env 文件存在但上次加载时不存在时，自动重新加载
    """
    global _settings, _loaded_env_mtime

    if _settings is None or reload:
        _settings = build_settings()
        _loaded_env_mtime = ENV_PATH.stat().st_mtime if ENV_PATH.exists() else None
        return _settings

    # .env 文件在首次加载后被创建，自动重新加载
    if ENV_PATH.exists() and _loaded_env_mtime is None:
        _logger.debug(".env 文件已创建，重新加载配置")
        _settings = build_settings()
        _loaded_env_mtime = ENV_PATH.stat().st_mtime
        return _settings

    return _settings


# 对外导出单例，方便其他模块一行拿到配置
settings: Settings = get_settings()


__all__ = [
    "Settings",
    "settings",
    "get_settings",
    "build_settings",
    "load_prompts",
    "ConfigError",
    "PROJECT_ROOT",
    "DEFAULT_SETTINGS_PATH",
    "ENV_PATH",
]


# ============================================================
# 直接运行本文件时的调试输出
# 用法：python -m core.config_loader
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        s = get_settings(reload=True)
        print(s.summary())
        print("\n（本模块可在其他代码中通过 `from core.config_loader import settings` 直接使用）")
    except ConfigError as e:
        print(str(e))
