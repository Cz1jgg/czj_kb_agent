# =========================================
#  RAG Chain：组装 retriever + prompt + LLM 并对外暴露 ask()
# =========================================
import logging
from typing import Any, Dict, List, Optional

from core.config_loader import Settings, get_settings, load_prompts
from core.document_parser import Document
from core.vector_store import VectorStoreManager, VectorStoreError

# 日志
_logger = logging.getLogger(__name__)


class RagChain:
    """问答链：将检索器、提示词、LLM 组装为完整问答流程。"""

    def __init__(
        self,
        retriever=None,
        llm=None,
        qa_template: str = "",
        condense_template: str = "",
        settings: Optional[Settings] = None,
    ):
        """
        初始化问答链。

        参数：
            retriever: FAISS 返回的检索器（可调用对象）
            llm: LangChain ChatModel 实例（支持 invoke/astream）
            qa_template: 问答提示词模板（包含 {context} 和 {question}）
            condense_template: 问题重写模板（多轮对话用）
            settings: 配置对象（若未提供则自动获取）
        """
        self._settings = settings or get_settings()
        self._retriever = retriever
        self._llm = llm
        self._qa_template = qa_template or self._load_qa_template()
        self._condense_template = condense_template or self._load_condense_template()

        # 检查组件是否就绪
        self._validate()

    # -------- 加载提示词模板 --------
    def _load_qa_template(self) -> str:
        """从 prompts.yaml 加载问答模板。"""
        try:
            prompts = load_prompts()
            return prompts.get("qa_template", "{context}\n\n问题：{question}\n回答：")
        except Exception as e:
            _logger.warning("加载问答模板失败，使用默认模板：%s", e)
            return """你是一个专业的知识库问答助手。请仅基于下面检索到的【上下文】回答用户问题。
若上下文中没有答案，请直接回答："抱歉，未在知识库中找到相关内容。"
不要编造不在上下文中的信息。

【上下文】
{context}

用户问题：{question}
回答："""

    def _load_condense_template(self) -> str:
        """从 prompts.yaml 加载问题重写模板。"""
        try:
            prompts = load_prompts()
            return prompts.get("condense_template", "{chat_history}\n{question}")
        except Exception as e:
            _logger.warning("加载重写模板失败，使用默认模板：%s", e)
            return """请根据对话历史将用户最新问题重写为一个独立的、清晰的问题。
若没有对话历史，直接返回原问题。

对话历史：
{chat_history}
用户最新问题：{question}
独立问题："""

    # -------- 组件验证 --------
    def _validate(self) -> None:
        """验证组件是否就绪。"""
        if self._retriever is None:
            _logger.warning("⚠️  Retriever 未设置，问答时将使用空上下文")
        if self._llm is None:
            _logger.warning("⚠️  LLM 未设置，问答功能将不可用")

    # -------- 工具：文档转来源列表 --------
    @staticmethod
    def _docs_to_sources(docs: List[Document]) -> List[Dict[str, Any]]:
        """
        **不依赖 LLM 生成来源**：
        直接从检索命中的 doc.metadata 提取信息，避免模型自由编造来源编号。
        """
        sources: List[Dict[str, Any]] = []
        for idx, doc in enumerate(docs):
            meta = doc.metadata or {}
            sources.append({
                "id": idx,
                "doc_id": meta.get("source") or meta.get("filename"),
                "title": meta.get("filename"),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index"),
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            })
        return sources

    # -------- 工具：构建上下文 --------
    def _build_context(self, docs: List[Document], max_tokens: int = 3000) -> str:
        """
        将检索文档拼接为上下文字符串，控制总长度。

        参数：
            docs: 检索到的文档列表
            max_tokens: 上下文最大长度（字符数）

        返回：
            拼接后的上下文文本
        """
        chunks = []
        total_len = 0

        for doc in docs:
            content = doc.page_content.strip()
            if not content:
                continue

            # 添加文档标记
            meta = doc.metadata or {}
            source_info = f"【来源：{meta.get('filename', '未知')}"
            if page := meta.get("page"):
                source_info += f" 第{page}页"
            source_info += "】\n"

            # 控制长度
            remaining = max_tokens - total_len - len(source_info) - 3  # 预留换行符
            if remaining <= 0:
                break

            # 截取内容
            if len(content) > remaining:
                content = content[:remaining] + "..."

            chunks.append(f"{source_info}{content}")
            total_len += len(source_info) + len(content)

        return "\n\n".join(chunks)

    # -------- 问答入口 --------
    def ask(
        self,
        question: str,
        top_k: Optional[int] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        执行一次问答，返回结构化结果。

        参数：
            question: 用户问题
            top_k: 检索文档数（默认从配置读取）
            chat_history: 对话历史（[{"user": "...", "assistant": "..."}, ...]）

        返回：
            {"answer": str, "sources": [...], "context": str}
        """
        # 1) 参数准备
        _top_k = top_k or self._settings.vector_store.top_k

        # 2) 验证 LLM 是否就绪
        if self._llm is None:
            return {
                "answer": "❌ 问答功能暂不可用：LLM 模型未初始化。请检查 API Key 配置。",
                "sources": [],
                "context": "",
            }

        try:
            # 3) 检索文档（如有 retriever）
            retrieved_docs: List[Document] = []
            if self._retriever:
                try:
                    # 调用检索器
                    results = self._retriever.invoke(question)
                    # 转换为 Document 对象
                    retrieved_docs = [
                        Document(page_content=r.page_content, metadata=r.metadata)
                        for r in results[:_top_k]
                    ]
                    _logger.debug("检索完成：%d 个文档", len(retrieved_docs))
                except Exception as e:
                    _logger.warning("检索失败，将使用空上下文：%s", e)
                    retrieved_docs = []

            # 4) 构建上下文
            context = self._build_context(retrieved_docs)

            # 5) 生成回答
            if context:
                prompt_text = self._qa_template.format(
                    context=context,
                    question=question,
                )
            else:
                # 无检索结果，直接回答
                prompt_text = f"请回答问题：{question}"

            _logger.debug("Prompt 长度：%d 字符", len(prompt_text))

            # 调用 LLM
            try:
                response = self._llm.invoke(prompt_text)
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as e:
                _logger.error("LLM 调用失败：%s", e)
                answer = f"❌ 调用 LLM 失败：{type(e).__name__}"

            # 6) 提取来源（直接从检索结果提取，不依赖 LLM）
            sources = self._docs_to_sources(retrieved_docs)

            # 7) 返回结果
            return {
                "answer": answer.strip(),
                "sources": sources,
                "context": context,
            }

        except Exception as e:
            _logger.error("问答流程异常：%s", e)
            return {
                "answer": f"❌ 问答处理失败：{type(e).__name__}",
                "sources": [],
                "context": "",
            }


# -------- 工厂函数：构建完整 RAG Chain --------
def build_rag_chain(settings: Optional[Settings] = None) -> RagChain:
    """
    根据配置构建完整的 RAG Chain。

    流程：
      1. 初始化向量库 → 获取检索器
      2. 初始化 LLM
      3. 加载提示词模板
      4. 组装 RagChain

    返回：
        RagChain 实例
    """
    _settings = settings or get_settings()

    # 1) 初始化向量库与检索器
    retriever = None
    try:
        vs_manager = VectorStoreManager()
        if vs_manager.exists():
            vs_manager.load()
            retriever = vs_manager.as_retriever()
            _logger.info("向量库已加载，创建检索器")
        else:
            _logger.warning("向量库不存在，将使用空检索器（仅直接回答问题）")
    except VectorStoreError as e:
        _logger.warning("向量库初始化失败：%s", e)

    # 2) 初始化 LLM（OpenAI 兼容接口）
    llm = None
    try:
        if not _settings.llm.api_key:
            _logger.warning("LLM API Key 未配置，跳过初始化")
        else:
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                _logger.warning("未安装 langchain-openai，跳过 LLM 初始化")
            else:
                llm = ChatOpenAI(
                    model=_settings.llm.model,
                    api_key=_settings.llm.api_key,
                    base_url=_settings.llm.base_url if hasattr(_settings.llm, "base_url") else None,
                    temperature=_settings.llm.temperature,
                    max_tokens=_settings.llm.max_tokens,
                    timeout=_settings.llm.timeout,
                )
                _logger.info("LLM 初始化完成：%s", _settings.llm.model)
    except Exception as e:
        _logger.error("LLM 初始化失败：%s", e)

    # 3) 构建 RagChain
    chain = RagChain(
        retriever=retriever,
        llm=llm,
        settings=_settings,
    )
    _logger.info("RagChain 构建完成")
    return chain


# ============================================================
# 导出
# ============================================================
__all__ = [
    "RagChain",
    "build_rag_chain",
]


# ============================================================
# 直接运行本文件时的调试输出
# ============================================================
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 构建链
    chain = build_rag_chain()

    # 测试问答
    question = "什么是 RAG？" if len(sys.argv) < 2 else sys.argv[1]
    print(f"\n问题：{question}")

    result = chain.ask(question)
    print(f"\n回答：\n{result['answer']}")

    if result["sources"]:
        print(f"\n引用来源（{len(result['sources'])} 个）：")
        for src in result["sources"]:
            print(f"  [{src['id']}] {src.get('title', '')}")
            print(f"    内容片段：{src.get('content', '')[:100]}...")
