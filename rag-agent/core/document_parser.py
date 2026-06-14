"""
文档解析模块：
TODO：基于 PyPDF2 / python-docx 实现 PDF、Word、TXT/Markdown 的文本抽取
"""
from typing import List


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}


def parse_document(file_path: str) -> str:
    """
    从文档中提取纯文本。
    TODO：实现 PDF / DOCX / TXT 的具体解析逻辑。
    """
    raise NotImplementedError("请在 core/document_parser.py 中实现真实解析逻辑。")


def batch_parse(file_paths: List[str]) -> List[str]:
    """批量解析，返回每个文件对应文本。"""
    return [parse_document(p) for p in file_paths]
