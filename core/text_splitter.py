# =========================================
#  文本分块：将 Document 列表按固定 chunk_size 切分
#  当前使用简易实现；后续可接入 langchain 的 RecursiveCharacterTextSplitter
# =========================================
from typing import List

from core.document_parser import Document


def split_documents(
    docs: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Document]:
    """
    简单的按字符数分块。
    - chunk_size:    每块字符数
    - chunk_overlap: 相邻块重叠字符数（避免语义被切开）
    """
    if chunk_size <= 0 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("分块参数不合法：需满足 chunk_size > chunk_overlap >= 0")

    chunks: List[Document] = []
    step = chunk_size - chunk_overlap

    for doc in docs:
        text = doc.page_content
        if not text:
            continue
        length = len(text)
        idx = 0
        part_no = 0
        while idx < length:
            piece = text[idx : idx + chunk_size]
            chunk_meta = dict(doc.metadata)
            chunk_meta["part"] = part_no
            chunks.append(Document(piece, chunk_meta))
            part_no += 1
            idx += step
    return chunks
