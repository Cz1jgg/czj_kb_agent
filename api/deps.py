# =========================================
#  全局依赖注入：配置单例 + RAG Chain 单例
#  对外使用方式：
#     from api.deps import get_app_settings, get_rag_chain
#     s = get_app_settings()
#     s.server.port   -> 8000
# =========================================
from core.config_loader import Settings, get_settings as _get_config_settings


# -------- 配置单例 --------
def get_app_settings() -> Settings:
    """获取全局配置单例（返回的是 core/config_loader.py 的 Settings 对象）。"""
    return _get_config_settings()


# -------- RAG Chain 单例（按需懒加载）--------
def get_rag_chain():
    """获取 RAG Chain 单例。"""
    # TODO：接入 FAISS + LLM 后打开
    # from core.rag_chain import build_rag_chain
    # return build_rag_chain(get_app_settings())
    return None
