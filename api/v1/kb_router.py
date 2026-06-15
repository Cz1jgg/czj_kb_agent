# =========================================
#  知识库管理路由：/api/v1/kb/*
#  提供：文档上传、索引重建、文档列表、删除
#  注：核心逻辑在 core/ 下，此处仅做路由骨架
# =========================================
from fastapi import APIRouter

router = APIRouter(prefix="/kb", tags=["知识库管理"])


@router.post("/upload")
def upload_document():
    """上传文档（后续接入 core.document_parser）。"""
    return {"status": "todo", "message": "文档上传接口（待接入解析逻辑）"}


@router.post("/rebuild")
def rebuild_index():
    """重建 FAISS 向量索引。"""
    return {"status": "todo", "message": "索引重建接口（待接入 vector_store）"}


@router.get("/docs")
def list_documents():
    """列出已入库的文档。"""
    return {"status": "todo", "message": "文档列表接口（待接入元数据）"}


@router.delete("/doc/{doc_id}")
def delete_document(doc_id: str):
    """删除指定文档。"""
    return {"status": "todo", "message": f"文档删除接口（待接入，doc_id={doc_id}）"}
