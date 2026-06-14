"""
RAG Agent 模块：
TODO：基于 LangChain 实现 RAG 问答链 / Agent
注意：sources 应当由程序基于检索 docs.metadata 显式生成，不要依赖 LLM 自由生成编号。
"""
from typing import List, Dict


class RAGAgent:
    """RAG 问答 Agent，对外返回 answer + sources。"""

    def __init__(self, llm=None, retriever=None):
        self.llm = llm
        self.retriever = retriever
        raise NotImplementedError("请在 core/rag_agent.py 中实现真实 Agent 逻辑。")

    def query(self, question: str, top_k: int = 4) -> Dict:
        """返回 {"answer": "...", "sources": [...]}。"""
        raise NotImplementedError
