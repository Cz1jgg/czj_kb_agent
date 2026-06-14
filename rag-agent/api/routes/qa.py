"""
问答路由：供 Java 服务调用的主要接口
（占位实现，真实 Agent 逻辑在 core/rag_agent.py）
"""
from fastapi import APIRouter
from api.schemas.schemas import QARequest, QAResponse

router = APIRouter(prefix="/api/qa", tags=["问答"])


@router.post("/query", response_model=QAResponse, summary="问答查询")
async def query_rag(req: QARequest):
    """TODO：接入 core/rag_agent.py 完成真实 RAG 问答。"""
    return QAResponse(
        query=req.query,
        answer="（占位）欢迎使用 RAG-Agent，请先配置 LLM 并构建向量库。",
        sources=[],
        top_k=req.top_k or 4,
    )
