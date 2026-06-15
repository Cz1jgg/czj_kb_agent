# =========================================
#  文档解析：PDF / Word / Markdown / TXT -> LangChain Document 列表
#  当前提供基础骨架 + 本地简单实现，后续可按需接入 langchain loader
# =========================================
import os
from pathlib import Path
from typing import List

# 用简单的数据结构代替 langchain.schema.Document，避免依赖问题
class Document:
    """简化版文档对象。"""
    def __init__(self, page_content: str, metadata: dict = None):
        self.page_content = page_content
        self.metadata = metadata or {}


# 支持的扩展名
SUPPORTED_EXT = {".pdf", ".docx", ".doc", ".md", ".txt"}


def parse_file(file_path: str) -> List[Document]:
    """
    解析单个文件，返回 Document 列表。
    - PDF:  按简单文本读取（PyPDF2）
    - DOCX: python-docx 按段落读
    - MD / TXT: 直接读全文
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")

    docs: List[Document] = []
    meta = {"source": str(path), "filename": path.name}

    if ext == ".pdf":
        # 使用 PyPDF2 读取 PDF 文本
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise RuntimeError("未安装 PyPDF2，请执行：pip install PyPDF2")
        reader = PdfReader(str(path))
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                docs.append(Document(text, {**meta, "page": idx + 1}))

    elif ext in (".docx", ".doc"):
        try:
            from docx import Document as DocxDocument
        except ImportError:
            raise RuntimeError("未安装 python-docx，请执行：pip install python-docx")
        doc = DocxDocument(str(path))
        text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(text_parts)
        if text.strip():
            docs.append(Document(text, meta))

    elif ext in (".md", ".txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            docs.append(Document(text, meta))
    else:
        raise ValueError(f"不支持的文件类型：{ext}，支持：{sorted(SUPPORTED_EXT)}")

    return docs


def parse_directory(dir_path: str) -> List[Document]:
    """递归解析目录下所有支持的文件。"""
    all_docs: List[Document] = []
    for root, _, files in os.walk(dir_path):
        for name in files:
            ext = os.path.splitext(name)[1].lower()
            if ext in SUPPORTED_EXT:
                all_docs.extend(parse_file(os.path.join(root, name)))
    return all_docs
