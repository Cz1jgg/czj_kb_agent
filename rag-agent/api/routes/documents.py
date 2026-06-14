"""
文档路由：上传 / 列表 / 删除
（占位实现，用于框架联调，真实解析逻辑在 core/document_parser.py）
"""
import uuid
import os

from fastapi import APIRouter, UploadFile, File, HTTPException
from api.schemas.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentInfo,
)

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

# 默认上传目录（保持路径相对，不引入复杂配置模块）
UPLOAD_DIR = os.path.join("data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse, summary="上传文档")
async def upload_document(file: UploadFile = File(...)):
    """上传文件到 data/uploads。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    file_id = uuid.uuid4().hex
    ext = os.path.splitext(file.filename)[1].lower()
    saved_name = f"{file_id}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)

    content = await file.read()
    with open(saved_path, "wb") as f:
        f.write(content)

    return DocumentUploadResponse(
        file_id=file_id,
        filename=file.filename,
        size_bytes=len(content),
        saved_path=saved_path,
    )


@router.get("/", response_model=DocumentListResponse, summary="文档列表")
async def list_documents():
    """简单列出上传目录中的文件。"""
    items = []
    if os.path.isdir(UPLOAD_DIR):
        for name in os.listdir(UPLOAD_DIR):
            path = os.path.join(UPLOAD_DIR, name)
            if os.path.isfile(path):
                items.append(
                    DocumentInfo(
                        file_id=os.path.splitext(name)[0],
                        filename=name,
                        saved_path=path,
                        size_bytes=os.path.getsize(path),
                    )
                )
    return DocumentListResponse(total=len(items), items=items)
