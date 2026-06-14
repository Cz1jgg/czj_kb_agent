"""
向量库路由：构建/重建 FAISS 索引
（占位实现，真实逻辑在 core/vectorstore.py）
"""
from fastapi import APIRouter
from api.schemas.schemas import BuildVectorRequest, BuildVectorResponse

router = APIRouter(prefix="/api/vectorstore", tags=["向量库"])


@router.post("/build", response_model=BuildVectorResponse, summary="构建/重建向量库")
async def build_vectorstore(req: BuildVectorRequest):
    """TODO：接入 core/vectorstore.py，对已解析文档执行 FAISS 索引构建。"""
    return BuildVectorResponse(
        status="success",
        chunk_count=0,
        message="占位响应：请在 core/vectorstore.py 实现真实索引构建逻辑。",
    )
