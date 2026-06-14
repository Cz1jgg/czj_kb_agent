"""
请求/响应 Pydantic 模型。
统一与 Java 服务对接的数据契约。
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# =====================
# 文档相关
# =====================
class DocumentUploadResponse(BaseModel):
    """文档上传返回。"""
    file_id: str = Field(description="文件唯一ID")
    filename: str = Field(description="原始文件名")
    size_bytes: int = Field(description="文件大小（字节）")
    saved_path: str = Field(description="保存路径")


class DocumentInfo(BaseModel):
    file_id: str
    filename: str
    saved_path: str
    size_bytes: int


class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentInfo]


# =====================
# 向量库相关
# =====================
class BuildVectorRequest(BaseModel):
    """重建向量库请求。"""
    file_ids: Optional[List[str]] = Field(default=None, description="指定文件；为空则使用全部已处理文档")


class BuildVectorResponse(BaseModel):
    status: str = Field(description="构建结果：success/failed")
    chunk_count: int = Field(description="入库分块数")
    message: Optional[str] = None


# =====================
# 问答相关
# =====================
class QARequest(BaseModel):
    """问答请求（Java 服务主要调用的入参）。"""
    query: str = Field(description="用户问题")
    top_k: Optional[int] = Field(default=4, description="检索返回的片段数")
    use_agent: Optional[bool] = Field(default=True, description="是否启用 Agent 处理")


class QAResponse(BaseModel):
    """问答响应：answer + 引用来源，来源由程序基于检索生成。"""
    query: str
    answer: str
    sources: List[str] = Field(description="检索到的文档来源列表")
    top_k: int
