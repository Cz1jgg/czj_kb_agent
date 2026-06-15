# =========================================
#  问答路由：POST /api/v1/qa/ask
#  Java 服务主要调用该接口进行问答
# =========================================
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/qa", tags=["问答"])


class AskRequest(BaseModel):
    """问答请求体：Java 服务按此 JSON 结构 POST。"""
    question: str
    kb_id: Optional[str] = "default"
    top_k: Optional[int] = 4


class SourceItem(BaseModel):
    """引用来源结构。"""
    doc_id: Optional[str] = None
    title: Optional[str] = None
    page: Optional[int] = None


class AskResponse(BaseModel):
    """问答响应体。"""
    answer: str
    sources: List[SourceItem] = []


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    问答接口（骨架）。
    真实逻辑：调用 core.rag_chain 获取 answer + sources。
    """
    return AskResponse(
        answer="知识库问答核心逻辑待接入（core.rag_chain）。",
        sources=[],
    )
