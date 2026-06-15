# =========================================
#  FAISS 向量库管理模块
#
#  功能：
#    - 初始化 FAISS 向量库（创建新库 / 加载已有库）
#    - add_documents：将分块后的 Document 存入向量库
#    - save / load：持久化向量库到磁盘
#    - as_retriever：返回检索器对象
#    - similarity_search：相似度检索
#    - 异常捕获：路径不存在、向量库损坏
#
#  使用方式：
#    from core.vector_store import VectorStoreManager
#    manager = VectorStoreManager()
#    manager.add_documents(chunks)
#    manager.save()
#    retriever = manager.as_retriever()
#    docs = manager.similarity_search("如何重置密码")
# =========================================
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.config_loader import settings
from core.document_parser import Document

# 日志
_logger = logging.getLogger(__name__)


# ============================================================
# 异常类
# ============================================================
class VectorStoreError(Exception):
    """向量库操作异常基类。"""
    pass


class VectorStoreNotFoundError(VectorStoreError):
    """向量库目录不存在或未初始化。"""
    pass


class VectorStoreCorruptedError(VectorStoreError):
    """向量库文件损坏或无法读取。"""
    pass


class EmbeddingModelError(VectorStoreError):
    """Embedding 模型初始化失败。"""
    pass


# ============================================================
# Embedding 模型封装（兼容 LangChain + 火山方舟 / OpenAI 接口）
# ============================================================
def _build_embeddings(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """
    构造 Embedding 模型实例。

    参数：
        provider: 提供商（默认从 settings 读取）
        model: 模型名（默认从 settings 读取）
        api_key: API Key（默认从 settings 读取）
        base_url: API 地址（默认从 settings 读取）

    返回：
        LangChain 兼容的 Embeddings 实例
    """
    _provider = provider or settings.embeddings.provider
    _model = model or settings.embeddings.model
    _api_key = api_key or settings.embeddings.api_key
    _base_url = base_url or ""  # Embedding 通常不需要 base_url

    if not _api_key:
        raise EmbeddingModelError(
            "❌ Embedding API Key 未配置（请在 .env 中设置 ARK_API_KEY 或 OPENAI_API_KEY）"
        )

    try:
        if _provider in ("openai", "dashscope", "volcengine"):
            # OpenAI 兼容接口（火山方舟 / 通义 / DeepSeek 等均通过此方式接入）
            try:
                from langchain_openai import OpenAIEmbeddings
            except ImportError:
                raise EmbeddingModelError(
                    "❌ 未安装 langchain-openai，请执行：pip install langchain-openai"
                )

            return OpenAIEmbeddings(
                model=_model,
                api_key=_api_key,
                base_url=_base_url if _base_url else None,
            )
        else:
            raise EmbeddingModelError(f"❌ 不支持的 Embedding provider：{_provider}")

    except EmbeddingModelError:
        raise
    except Exception as e:
        raise EmbeddingModelError(
            f"❌ Embedding 模型初始化失败：{type(e).__name__}: {e}"
        ) from e


# ============================================================
# Document 转换：将简化 Document 转为 LangChain Document
# ============================================================
def _to_langchain_doc(doc: Document) -> "langchain_core.documents.base.Document":
    """
    将简化 Document 转换为 LangChain Document。
    延迟导入避免全局依赖。
    """
    from langchain_core.documents.base import Document as LCDocument
    return LCDocument(
        page_content=doc.page_content,
        metadata=doc.metadata or {},
    )


def _to_simple_doc(doc: Any) -> Document:
    """将 LangChain Document 或其他文档对象转换为简化 Document。"""
    if isinstance(doc, Document):
        return doc
    return Document(
        page_content=getattr(doc, "page_content", str(doc)),
        metadata=getattr(doc, "metadata", {}) or {},
    )


# ============================================================
# FAISS 向量库管理器
# ============================================================
class VectorStoreManager:
    """
    FAISS 向量库管理器。

    功能：
        - build_from_documents：从 Document 列表构建向量库
        - add_documents：增量添加文档
        - save：持久化到磁盘
        - load：从磁盘加载
        - similarity_search：向量检索
        - as_retriever：返回 LangChain Retriever

    示例：
        manager = VectorStoreManager()
        manager.build_from_documents(chunks)  # 首次构建
        manager.save()

        manager2 = VectorStoreManager()
        manager2.load()                       # 加载已有
        results = manager2.similarity_search("查询内容")
    """

    # FAISS 持久化文件名（LangChain 固定命名）
    INDEX_FILE = "index.faiss"
    DOCSTORE_FILE = "index.pkl"

    def __init__(
        self,
        vector_store_dir: Optional[str] = None,
        embeddings=None,
        embeddings_provider: Optional[str] = None,
        embeddings_model: Optional[str] = None,
    ):
        """
        初始化向量库管理器。

        参数：
            vector_store_dir: 持久化目录（默认从 settings.vector_store.path 读取）
            embeddings: 已有 Embedding 实例（可选，未提供则自动构造）
            embeddings_provider: Embedding 提供商（可选）
            embeddings_model: Embedding 模型名（可选）
        """
        self._dir = vector_store_dir or settings.vector_store.path

        # 初始化 Embedding 模型
        if embeddings is not None:
            self._embeddings = embeddings
        else:
            self._embeddings = _build_embeddings(
                provider=embeddings_provider,
                model=embeddings_model,
            )

        # FAISS 实例
        self._store: Optional[Any] = None

        # 确保目录存在
        Path(self._dir).mkdir(parents=True, exist_ok=True)

        _logger.info("VectorStoreManager 初始化完成，目录：%s", self._dir)

    # ------------------ 属性 ------------------
    @property
    def store_dir(self) -> str:
        """向量库持久化目录。"""
        return self._dir

    @property
    def is_loaded(self) -> bool:
        """向量库是否已加载。"""
        return self._store is not None

    @property
    def doc_count(self) -> int:
        """向量库中当前文档数量。"""
        if self._store is None:
            return 0
        try:
            return self._store.index.ntotal  # type: ignore
        except Exception:
            return 0

    # ------------------ 核心方法 ------------------
    def build_from_documents(
        self,
        docs: List[Document],
        allow_dangerous_deserialization: bool = True,
    ) -> None:
        """
        从 Document 列表构建新的 FAISS 向量库（会覆盖已有索引）。

        参数：
            docs: 分块后的 Document 列表
            allow_dangerous_deserialization: 允许加载 pickle（LangChain 安全要求）
        """
        if not docs:
            raise VectorStoreError("❌ 待构建的文档列表为空，请先调用 document_parser + text_splitter")

        _logger.info("开始构建向量库：%d 个 Document", len(docs))

        try:
            from langchain_community.vectorstores import FAISS

            # 转换为 LangChain Document
            lc_docs = [_to_langchain_doc(d) for d in docs]

            # 构建 FAISS 索引
            self._store = FAISS.from_documents(
                documents=lc_docs,
                embedding=self._embeddings,
            )

            _logger.info(
                "向量库构建完成：%d 个向量，目录：%s",
                self.doc_count, self._dir
            )

        except Exception as e:
            raise VectorStoreCorruptedError(
                f"❌ 向量库构建失败：{type(e).__name__}: {e}\n"
                f"   常见原因：Embedding 模型不可用 / API Key 无效"
            ) from e

    def add_documents(
        self,
        docs: List[Document],
    ) -> int:
        """
        向已有向量库增量添加文档。

        参数：
            docs: 待添加的 Document 列表

        返回：
            新增的向量数量
        """
        if not docs:
            return 0

        if self._store is None:
            # 库未初始化，自动构建
            _logger.warning("向量库未初始化，自动从文档构建")
            self.build_from_documents(docs)
            return self.doc_count

        try:
            from langchain_community.vectorstores import FAISS

            lc_docs = [_to_langchain_doc(d) for d in docs]
            before_count = self.doc_count

            # 增量添加
            self._store.add_documents(lc_docs)

            after_count = self.doc_count
            _logger.info(
                "文档添加完成：新增 %d 个向量，当前总数 %d",
                after_count - before_count, after_count
            )
            return after_count - before_count

        except Exception as e:
            raise VectorStoreError(
                f"❌ 增量添加文档失败：{type(e).__name__}: {e}"
            ) from e

    # ------------------ 持久化 ------------------
    def save(self) -> str:
        """
        将向量库持久化到磁盘。

        返回：
            持久化目录路径

        异常：
            VectorStoreError: 向量库未初始化或保存失败
        """
        if self._store is None:
            raise VectorStoreError("❌ 向量库未初始化，无法保存（请先调用 build_from_documents 或 load）")

        try:
            self._store.save_local(self._dir)
            _logger.info("向量库已保存到：%s", self._dir)
            return self._dir
        except Exception as e:
            raise VectorStoreError(
                f"❌ 向量库保存失败：{type(e).__name__}: {e}\n"
                f"   目录：{self._dir}"
            ) from e

    def load(
        self,
        allow_dangerous_deserialization: bool = True,
    ) -> None:
        """
        从磁盘加载向量库。

        参数：
            allow_dangerous_deserialization: 允许加载 pickle（LangChain 安全要求）

        异常：
            VectorStoreNotFoundError: 索引文件不存在
            VectorStoreCorruptedError: 索引文件损坏
        """
        index_path = os.path.join(self._dir, self.INDEX_FILE)

        if not os.path.exists(index_path):
            raise VectorStoreNotFoundError(
                f"❌ 未找到向量库索引文件：{index_path}\n"
                f"   请先调用 build_from_documents + save 构建并保存向量库。"
            )

        try:
            from langchain_community.vectorstores import FAISS

            self._store = FAISS.load_local(
                self._dir,
                self._embeddings,
                allow_dangerous_deserialization=allow_dangerous_deserialization,
            )

            _logger.info(
                "向量库加载完成：%d 个向量，目录：%s",
                self.doc_count, self._dir
            )

        except Exception as e:
            raise VectorStoreCorruptedError(
                f"❌ 向量库加载失败（文件可能损坏）：{type(e).__name__}: {e}\n"
                f"   目录：{self._dir}"
            ) from e

    def exists(self) -> bool:
        """检查向量库是否已存在（磁盘上有持久化文件）。"""
        index_path = os.path.join(self._dir, self.INDEX_FILE)
        return os.path.exists(index_path)

    # ------------------ 检索 ------------------
    def similarity_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        向量相似度检索。

        参数：
            query: 查询文本
            top_k: 返回的最相关文档数（默认从 settings.vector_store.top_k 读取）
            filter_metadata: 按 metadata 过滤（如 {"filename": "xxx.pdf"}）

        返回：
            List[Document]: 最相关的 Document 列表
        """
        if self._store is None:
            raise VectorStoreError(
                "❌ 向量库未加载，请先调用 load() 或 build_from_documents()"
            )

        _top_k = top_k or settings.vector_store.top_k
        _score_threshold = settings.vector_store.score_threshold

        try:
            if filter_metadata:
                results = self._store.similarity_search_with_score(
                    query,
                    k=_top_k,
                    filter=filter_metadata,
                )
                # 过滤低分结果
                docs_with_score = [
                    (doc, score)
                    for doc, score in results
                    if _score_threshold == 0.0 or score <= _score_threshold
                ]
                lc_docs = [doc for doc, _ in docs_with_score]
            else:
                lc_docs = self._store.similarity_search(
                    query,
                    k=_top_k,
                )

            # 转换为简化 Document
            simple_docs = [_to_simple_doc(d) for d in lc_docs]

            _logger.debug(
                "检索完成：query='%s' -> %d 个结果",
                query[:50], len(simple_docs)
            )
            return simple_docs

        except Exception as e:
            raise VectorStoreError(
                f"❌ 检索失败：{type(e).__name__}: {e}"
            ) from e

    def as_retriever(
        self,
        top_k: Optional[int] = None,
        search_type: str = "similarity",
        filter_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        返回 LangChain Retriever 对象，可直接用于 RAG Chain。

        参数：
            top_k: 返回文档数（默认从 settings.vector_store.top_k 读取）
            search_type: 检索类型（"similarity" / "mmr"）
            filter_metadata: 按 metadata 过滤

        返回：
            LangChain Retriever 对象
        """
        if self._store is None:
            raise VectorStoreError("❌ 向量库未加载，请先调用 load() 或 build_from_documents()")

        _top_k = top_k or settings.vector_store.top_k

        try:
            retriever = self._store.as_retriever(
                search_type=search_type,
                search_kwargs={
                    "k": _top_k,
                    "score_threshold": settings.vector_store.score_threshold,
                    "filter": filter_metadata,
                },
            )
            _logger.debug("Retriever 创建完成：top_k=%d, search_type=%s", _top_k, search_type)
            return retriever
        except Exception as e:
            raise VectorStoreError(
                f"❌ Retriever 创建失败：{type(e).__name__}: {e}"
            ) from e

    # ------------------ 管理 ------------------
    def delete(self) -> None:
        """删除磁盘上的向量库文件（谨慎使用）。"""
        import shutil

        if os.path.exists(self._dir):
            shutil.rmtree(self._dir)
            _logger.warning("向量库已删除：%s", self._dir)

    def reset(self) -> None:
        """重置内存中的向量库（不清除磁盘文件）。"""
        self._store = None
        _logger.info("向量库已重置（内存）")

    def info(self) -> Dict[str, Any]:
        """返回向量库状态信息。"""
        return {
            "dir": self._dir,
            "is_loaded": self.is_loaded,
            "doc_count": self.doc_count,
            "exists_on_disk": self.exists(),
            "embeddings_model": getattr(self._embeddings, "model", "unknown"),
        }


# ============================================================
# 导出
# ============================================================
__all__ = [
    "VectorStoreManager",
    "VectorStoreError",
    "VectorStoreNotFoundError",
    "VectorStoreCorruptedError",
    "EmbeddingModelError",
]


# ============================================================
# 直接运行本文件时的调试输出
# 用法：python -m core.vector_store
# ============================================================
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 尝试初始化（API Key 未配置时会抛出 EmbeddingModelError）
    try:
        manager = VectorStoreManager()
        print("\n向量库信息：")
        for k, v in manager.info().items():
            print(f"  {k}: {v}")
        print("\n✅ VectorStoreManager 已初始化，可调用 manager.load() 或 manager.build_from_documents()")
        print(f"   持久化目录：{manager.store_dir}")
    except EmbeddingModelError as e:
        print(str(e))
        print("\n⚠️  Embedding API Key 未配置，向量库无法初始化。")
        print("   请复制 .env.example 为 .env，填入 ARK_API_KEY 后重试。")
