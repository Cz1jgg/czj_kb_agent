# =========================================
#  RAG Chain：组装 retriever + prompt + LLM 并对外暴露 ask()
#  当前仅为骨架 + 返回结构示例，真实 LLM 与 retriever 后续接入
# =========================================
from typing import List, Dict, Any

from core.document_parser import Document


class RagChain:
    """问答链。"""

    def __init__(self, retriever=None, llm=None, qa_template: str = ""):
        self.retriever = retriever  # FAISS 返回的检索器
        self.llm = llm              # LangChain ChatModel 实例
        self.qa_template = qa_template or "{context}\n{question}"

    # -------- 工具：把检索文档元数据转为 sources --------
    @staticmethod
    def _docs_to_sources(docs: List[Document]) -> List[Dict[str, Any]]:
        """
        **不依赖 LLM 生成来源**：
        直接从检索命中的 doc.metadata 提取 doc_id / title / page，
        避免让模型自由编造来源编号。
        """
        sources: List[Dict[str, Any]] = []
        for doc in docs:
            meta = doc.metadata or {}
            sources.append({
                "doc_id": meta.get("source") or meta.get("filename"),
                "title": meta.get("filename"),
                "page": meta.get("page"),
            })
        return sources

    # -------- 问答入口 --------
    def ask(self, question: str, top_k: int = 4) -> Dict[str, Any]:
        """
        执行一次问答，返回 {"answer": str, "sources": [...]}。
        当前为占位实现，实际接入 LLM + retriever 后替换。
        """
        # 真实实现示意（待接入）：
        # docs = self.retriever.invoke(question)  # 只取前 top_k 个
        # context = "\n\n".join(d.page_content for d in docs)
        # prompt_text = self.qa_template.format(context=context, question=question)
        # answer = self.llm.invoke(prompt_text)
        # sources = self._docs_to_sources(docs)
        # return {"answer": answer, "sources": sources}

        # --- 占位返回：不依赖真实模型 ---
        return {
            "answer": "（RagChain 占位回答）请接入 LLM 与 FAISS 后使用。",
            "sources": [],
        }


# -------- 工厂函数 --------
def build_rag_chain(settings: dict):
    """根据 settings 构造 RagChain 实例（当前仅初始化，真实组件待接入）。"""
    # TODO: 初始化 embeddings / vector_store / retriever / llm / qa_template
    template = ""  # 可从 core.config_loader.load_prompts()["qa_template"] 读取
    return RagChain(retriever=None, llm=None, qa_template=template)
