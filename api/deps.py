# =========================================
#  全局依赖注入
#  提供：配置单例、RAG Chain 单例
# =========================================
from core.config_loader import load_settings

# 全局配置单例（仅在首次导入时加载一次）
_settings = None


def get_settings():
    """获取全局配置（单例）。"""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def get_rag_chain():
    """获取 RAG Chain 单例（按需懒加载）。"""
    # 预留位置：接入 FAISS + LLM 后在此返回链实例
    # from core.rag_chain import build_rag_chain
    # return build_rag_chain(get_settings())
    return None
