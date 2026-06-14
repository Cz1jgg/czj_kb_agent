"""
向量库模块：
TODO：接入 langchain_community.vectorstores.FAISS 实现 build / save / load / similarity_search
"""
from typing import List, Optional

try:
    from langchain_core.documents import Document  # 仅类型提示
except Exception:
    Document = dict  # 兼容兜底


class VectorStore:
    """FAISS 向量库的统一接口。"""

    def __init__(self, index_path: str = "data/faiss_index"):
        self.index_path = index_path
        raise NotImplementedError("请在 core/vectorstore.py 中实现 FAISS 真实构建/检索逻辑。")

    def build_from_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError

    @classmethod
    def load(cls, index_path: str):
        raise NotImplementedError

    def similarity_search(self, query: str, k: int = 4):
        raise NotImplementedError
