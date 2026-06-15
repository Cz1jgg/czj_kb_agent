# =========================================
#  FAISS 向量库管理（占位实现）
#  - 提供 build / save / load / as_retriever 接口
#  - 当前仅完成框架，真实向量模型与 FAISS 后续接入
# =========================================
import os
from pathlib import Path
from typing import List, Optional

from core.document_parser import Document


class VectorStoreManager:
    """FAISS 向量库管理器。"""

    def __init__(self, vector_store_dir: str, embeddings=None):
        """
        vector_store_dir: FAISS 索引的持久化目录（data/vector_store）
        embeddings:       可选，Embedding 模型实例（接入 LangChain 时使用）
        """
        self.vector_store_dir = vector_store_dir
        self.embeddings = embeddings
        self._store = None  # 真实 FAISS 实例，待接入
        Path(self.vector_store_dir).mkdir(parents=True, exist_ok=True)

    # -------- 构建 --------
    def build(self, docs: List[Document]) -> None:
        """
        基于 Document 列表构建 FAISS 索引。
        当前为空实现，待接入 langchain.vectorstores.FAISS.from_documents(...)。
        """
        # TODO: self._store = FAISS.from_documents(
        #     [doc_to_langchain(d) for d in docs], self.embeddings
        # )
        self._store = object()  # 先用占位，表示"已构建"

    # -------- 持久化 --------
    def save(self) -> None:
        """保存 FAISS 索引到 vector_store_dir。"""
        if self._store is None:
            raise RuntimeError("FAISS 索引尚未构建，无法 save")
        # TODO: self._store.save_local(self.vector_store_dir)
        # 这里留一个占位文件，方便识别目录状态
        marker = os.path.join(self.vector_store_dir, ".built")
        Path(marker).touch()

    def load(self) -> None:
        """从磁盘加载 FAISS 索引。"""
        # TODO: self._store = FAISS.load_local(
        #     self.vector_store_dir, self.embeddings, allow_dangerous_deserialization=True
        # )
        marker = os.path.join(self.vector_store_dir, ".built")
        if not os.path.exists(marker):
            raise FileNotFoundError(f"未找到索引标记：{marker}，请先 build + save")
        self._store = object()

    # -------- 检索 --------
    def as_retriever(self, top_k: int = 4):
        """返回检索器（当前占位，接入 FAISS 后返回 self._store.as_retriever()）。"""
        if self._store is None:
            raise RuntimeError("FAISS 索引未加载，请先 build() 或 load()")
        return None  # TODO: return self._store.as_retriever(search_kwargs={"k": top_k})

    def similarity_search(self, query: str, top_k: int = 4) -> List[Document]:
        """直接检索，返回 Document 列表（占位）。"""
        raise NotImplementedError("similarity_search 待接入真实 FAISS")
