# =========================================
#  问答路由：POST /api/v1/qa/ask
#  Java 服务主要调用该接口进行问答
# =========================================
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.rag_chain import RagChain, build_rag_chain
from core.config_loader import get_settings

router = APIRouter(prefix="/qa", tags=["问答"])

# 全局 RagChain 单例（懒加载）
_rag_chain: Optional[RagChain] = None

# 日志
_logger = logging.getLogger(__name__)


# -------- 请求模型 --------
class AskRequest(BaseModel):
    """问答请求体：Java 服务按此 JSON 结构 POST。"""
    question: str                    # 用户问题（必填）
    kb_id: Optional[str] = "default" # 知识库 ID（默认 default）
    top_k: Optional[int] = 4         # 检索文档数（默认 4）


# -------- 来源项模型 --------
class SourceItem(BaseModel):
    """引用来源结构。"""
    id: Optional[int] = None         # 来源索引
    doc_id: Optional[str] = None     # 文档 ID（文件名或路径）
    title: Optional[str] = None      # 文档标题（通常为文件名）
    page: Optional[int] = None       # PDF 页码
    chunk_index: Optional[int] = None # 分块索引
    content: Optional[str] = None    # 内容片段（用于预览）


# -------- 数据响应模型 --------
class AskResult(BaseModel):
    """问答结果数据。"""
    answer: str                      # 回答内容
    sources: List[SourceItem] = []   # 引用来源列表


# -------- 统一响应模型 --------
class ApiResponse(BaseModel):
    """统一 API 响应格式。"""
    code: int                        # 状态码：200 成功，其他为错误码
    message: str                     # 提示信息
    data: Optional[AskResult] = None # 数据（成功时有值）


# -------- 工具函数：获取 RagChain 单例 --------
def get_rag_chain() -> RagChain:
    """获取 RagChain 单例（懒加载）。"""
    global _rag_chain
    if _rag_chain is None:
        try:
            _rag_chain = build_rag_chain(get_settings())
            _logger.info("RagChain 单例初始化完成")
        except Exception as e:
            _logger.error("RagChain 初始化失败：%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"内部错误：RagChain 初始化失败"
            )
    return _rag_chain


# -------- 问答接口 --------
@router.post("/ask", response_model=ApiResponse, summary="问答接口")
def ask(req: AskRequest):
    """
    问答接口：接收用户问题，返回回答与引用来源。

    请求体：
    {
        "question": "用户问题",
        "kb_id": "知识库 ID（可选，默认 default）",
        "top_k": 4  // 检索文档数（可选，默认 4）
    }

    响应体：
    {
        "code": 200,
        "message": "success",
        "data": {
            "answer": "回答内容",
            "sources": [
                {"id": 0, "title": "文档名", "page": 3, "content": "片段..."}
            ]
        }
    }

    错误响应：
    {
        "code": 500,
        "message": "错误描述",
        "data": null
    }
    """
    # 1) 参数校验
    if not req.question or not req.question.strip():
        return ApiResponse(
            code=400,
            message="参数错误：question 不能为空",
            data=None
        )

    # 2) 获取 RagChain
    try:
        chain = get_rag_chain()
    except HTTPException as e:
        return ApiResponse(
            code=e.status_code,
            message=f"内部错误：{e.detail}",
            data=None
        )

    # 3) 执行问答
    try:
        _logger.info(f"收到问答请求：{req.question[:50]}...")

        result = chain.ask(
            question=req.question.strip(),
            top_k=req.top_k,
        )

        # 4) 转换来源格式
        sources = []
        for src in result.get("sources", []):
            sources.append(SourceItem(
                id=src.get("id"),
                doc_id=src.get("doc_id"),
                title=src.get("title"),
                page=src.get("page"),
                chunk_index=src.get("chunk_index"),
                content=src.get("content"),
            ))

        # 5) 返回成功响应
        return ApiResponse(
            code=200,
            message="success",
            data=AskResult(
                answer=result.get("answer", ""),
                sources=sources,
            )
        )

    except Exception as e:
        # 5) 返回错误响应
        _logger.error(f"问答失败：{e}")
        return ApiResponse(
            code=500,
            message=f"问答处理失败：{type(e).__name__}",
            data=None
        )


# -------- 健康检查（问答模块专用）--------
@router.get("/health", summary="问答模块健康检查")
def qa_health():
    """检查问答模块是否就绪（LLM 和向量库状态）。"""
    try:
        chain = get_rag_chain()
        settings = get_settings()

        # 检查组件状态
        llm_ready = True if chain._llm else False
        retriever_ready = True if chain._retriever else False

        return ApiResponse(
            code=200,
            message="success",
            data=AskResult(
                answer="问答模块健康检查通过",
                sources=[SourceItem(
                    id=0,
                    title="组件状态",
                    content=f"LLM: {'就绪' if llm_ready else '未就绪'}, Retriever: {'就绪' if retriever_ready else '未就绪'}, 模型: {settings.llm.model}"
                )]
            )
        )
    except Exception as e:
        return ApiResponse(
            code=503,
            message=f"问答模块未就绪：{str(e)}",
            data=None
        )
