# =========================================
#  知识库管理路由：/api/v1/kb/*
#  提供：文档上传、索引重建、文档列表、删除
# =========================================
import logging
import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from core.config_loader import get_settings
from core.document_parser import (
    Document,
    parse_file,
    parse_directory,
    UnsupportedFormatError,
    FileNotFoundError as DocFileNotFoundError,
)
from core.text_splitter import split_documents, estimate_chunk_count
from core.vector_store import (
    VectorStoreManager,
    VectorStoreError,
    VectorStoreNotFoundError,
)

router = APIRouter(prefix="/kb", tags=["知识库管理"])

# 日志
_logger = logging.getLogger(__name__)

# 统一响应模型
class ApiResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None


# -------- 文件上传接口 --------
class UploadResult(BaseModel):
    filename: str
    saved_path: str
    doc_count: int
    chunk_count: int


@router.post("/upload", response_model=ApiResponse, summary="上传文档")
def upload_document(file: UploadFile = File(...)):
    """
    上传文档并入库。
    
    流程：
      1. 接收文件，保存到 data/documents/
      2. 解析文件内容
      3. 文本分块
      4. 存入向量库
    
    请求：multipart/form-data，key 为 file
    
    响应：
    {
        "code": 200,
        "message": "success",
        "data": {
            "filename": "xxx.pdf",
            "saved_path": "data/documents/xxx.pdf",
            "doc_count": 1,
            "chunk_count": 10
        }
    }
    """
    settings = get_settings()
    upload_dir = Path(settings.upload.save_dir)

    try:
        # 1) 验证文件
        if not file.filename:
            return ApiResponse(code=400, message="文件名不能为空")

        filename = file.filename.strip()
        ext = Path(filename).suffix.lower()

        # 检查文件格式
        if ext not in settings.upload.allow_extensions:
            return ApiResponse(
                code=400,
                message=f"不支持的文件格式：{ext}，支持格式：{settings.upload.allow_extensions}"
            )

        # 2) 保存文件
        upload_dir.mkdir(parents=True, exist_ok=True)
        save_path = upload_dir / filename

        # 检查文件是否已存在
        if save_path.exists():
            _logger.warning("文件已存在，将覆盖：%s", save_path)

        # 写入文件
        contents = file.file.read()
        save_path.write_bytes(contents)
        _logger.info("文件保存成功：%s", save_path)

        # 3) 解析文件
        docs = parse_file(str(save_path))
        if not docs:
            return ApiResponse(code=400, message="文件内容为空或解析失败")

        # 4) 文本分块
        chunks = split_documents(docs)
        _logger.info("文件 %s 解析为 %d 个文档，分块为 %d 个 chunk", filename, len(docs), len(chunks))

        # 5) 存入向量库
        vs_manager = VectorStoreManager()
        added_count = vs_manager.add_documents(chunks)
        vs_manager.save()

        # 6) 返回结果
        return ApiResponse(
            code=200,
            message="success",
            data={
                "filename": filename,
                "saved_path": str(save_path),
                "doc_count": len(docs),
                "chunk_count": len(chunks),
                "added_to_vector_store": added_count,
            }
        )

    except UnsupportedFormatError as e:
        _logger.error("文件格式不支持：%s", e)
        return ApiResponse(code=400, message=f"文件格式不支持：{str(e)}")

    except DocFileNotFoundError as e:
        _logger.error("文件不存在：%s", e)
        return ApiResponse(code=404, message=f"文件不存在：{str(e)}")

    except VectorStoreError as e:
        _logger.error("向量库操作失败：%s", e)
        return ApiResponse(code=500, message=f"向量库操作失败：{str(e)}")

    except Exception as e:
        _logger.error("文件上传失败：%s", e)
        return ApiResponse(code=500, message=f"文件上传失败：{type(e).__name__}: {str(e)}")


# -------- 重建索引接口 --------
class RebuildResult(BaseModel):
    total_files: int
    total_docs: int
    total_chunks: int
    failed_files: List[str]


@router.post("/rebuild", response_model=ApiResponse, summary="重建索引")
def rebuild_index(clear_existing: bool = True):
    """
    重建向量索引（重新加载所有文档）。
    
    流程：
      1. 清空现有向量库（可选）
      2. 扫描 data/documents/ 下所有文件
      3. 解析、分块、入库
    
    参数：
        clear_existing: 是否清空现有索引（默认 True）
    
    响应：
    {
        "code": 200,
        "message": "success",
        "data": {
            "total_files": 5,
            "total_docs": 10,
            "total_chunks": 50,
            "failed_files": []
        }
    }
    """
    settings = get_settings()
    docs_dir = Path(settings.upload.save_dir)

    try:
        # 1) 检查目录
        if not docs_dir.exists():
            return ApiResponse(code=404, message=f"文档目录不存在：{docs_dir}")

        # 2) 清空现有向量库
        vs_manager = VectorStoreManager()
        if clear_existing and vs_manager.exists():
            vs_manager.delete()
            vs_manager.reset()
            _logger.info("已清空现有向量库")

        # 3) 解析目录下所有文件
        all_docs = parse_directory(str(docs_dir))
        if not all_docs:
            return ApiResponse(code=400, message="未找到可解析的文档")

        # 4) 文本分块
        chunks = split_documents(all_docs)
        _logger.info("共解析 %d 个文档，分块为 %d 个 chunk", len(all_docs), len(chunks))

        # 5) 构建新索引
        vs_manager.build_from_documents(chunks)
        vs_manager.save()

        # 6) 返回结果
        return ApiResponse(
            code=200,
            message="success",
            data={
                "total_files": len([f for f in docs_dir.iterdir() if f.is_file()]),
                "total_docs": len(all_docs),
                "total_chunks": len(chunks),
                "failed_files": [],
            }
        )

    except VectorStoreError as e:
        _logger.error("向量库操作失败：%s", e)
        return ApiResponse(code=500, message=f"向量库操作失败：{str(e)}")

    except Exception as e:
        _logger.error("重建索引失败：%s", e)
        return ApiResponse(code=500, message=f"重建索引失败：{type(e).__name__}: {str(e)}")


# -------- 文件列表接口 --------
class FileInfo(BaseModel):
    filename: str
    path: str
    size: int
    modified_at: str


@router.get("/list", response_model=ApiResponse, summary="文档列表")
def list_documents():
    """
    获取已上传的文档列表。
    
    响应：
    {
        "code": 200,
        "message": "success",
        "data": {
            "files": [
                {"filename": "xxx.pdf", "path": "...", "size": 1024, "modified_at": "2024-01-01 12:00:00"},
                ...
            ],
            "total": 5
        }
    }
    """
    settings = get_settings()
    docs_dir = Path(settings.upload.save_dir)

    try:
        # 检查目录
        if not docs_dir.exists():
            return ApiResponse(
                code=200,
                message="success",
                data={"files": [], "total": 0}
            )

        # 遍历文件
        files_info = []
        for item in docs_dir.iterdir():
            if item.is_file():
                files_info.append({
                    "filename": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                    "modified_at": item.stat().st_mtime,
                })

        # 按修改时间排序（最新在前）
        files_info.sort(key=lambda x: x["modified_at"], reverse=True)

        # 格式化时间
        for f in files_info:
            from datetime import datetime
            f["modified_at"] = datetime.fromtimestamp(f["modified_at"]).strftime("%Y-%m-%d %H:%M:%S")

        return ApiResponse(
            code=200,
            message="success",
            data={
                "files": files_info,
                "total": len(files_info),
            }
        )

    except Exception as e:
        _logger.error("获取文档列表失败：%s", e)
        return ApiResponse(code=500, message=f"获取文档列表失败：{type(e).__name__}: {str(e)}")


# -------- 删除文档接口 --------
@router.delete("/doc/{doc_id}", response_model=ApiResponse, summary="删除文档")
def delete_document(doc_id: str):
    """
    删除指定文档（同时从磁盘和向量库移除）。
    
    注意：当前实现仅删除磁盘文件，如需从向量库删除对应向量，需要重建索引。
    
    参数：
        doc_id: 文档文件名（如 xxx.pdf）
    
    响应：
    {
        "code": 200,
        "message": "success",
        "data": {"deleted": "xxx.pdf"}
    }
    """
    settings = get_settings()
    docs_dir = Path(settings.upload.save_dir)
    file_path = docs_dir / doc_id

    try:
        # 检查文件是否存在
        if not file_path.exists():
            return ApiResponse(code=404, message=f"文档不存在：{doc_id}")

        # 删除文件
        file_path.unlink()
        _logger.info("已删除文件：%s", file_path)

        # 提示需要重建索引
        _logger.warning("文件已删除，但向量库未更新，建议调用 /api/v1/kb/rebuild 重建索引")

        return ApiResponse(
            code=200,
            message="success",
            data={
                "deleted": doc_id,
                "note": "文件已删除，建议调用 rebuild 接口重建索引以更新向量库"
            }
        )

    except Exception as e:
        _logger.error("删除文档失败：%s", e)
        return ApiResponse(code=500, message=f"删除文档失败：{type(e).__name__}: {str(e)}")


# -------- 向量库状态接口 --------
@router.get("/status", response_model=ApiResponse, summary="向量库状态")
def get_kb_status():
    """
    获取知识库状态（向量库大小、文档数等）。
    
    响应：
    {
        "code": 200,
        "message": "success",
        "data": {
            "vector_store_exists": true,
            "doc_count": 100,
            "documents_dir": "data/documents",
            "vector_store_dir": "data/vector_store"
        }
    }
    """
    settings = get_settings()

    try:
        vs_manager = VectorStoreManager()
        vector_store_exists = vs_manager.exists()
        
        if vector_store_exists:
            try:
                vs_manager.load()
                doc_count = vs_manager.doc_count
            except VectorStoreError:
                doc_count = 0
        else:
            doc_count = 0

        # 统计上传目录的文件数
        docs_dir = Path(settings.upload.save_dir)
        file_count = len([f for f in docs_dir.iterdir() if f.is_file()]) if docs_dir.exists() else 0

        return ApiResponse(
            code=200,
            message="success",
            data={
                "vector_store_exists": vector_store_exists,
                "doc_count": doc_count,
                "uploaded_files_count": file_count,
                "documents_dir": str(docs_dir),
                "vector_store_dir": vs_manager.store_dir,
            }
        )

    except Exception as e:
        _logger.error("获取知识库状态失败：%s", e)
        return ApiResponse(code=500, message=f"获取知识库状态失败：{type(e).__name__}: {str(e)}")