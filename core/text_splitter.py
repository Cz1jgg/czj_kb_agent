# =========================================
#  文本分块模块：基于 LangChain RecursiveCharacterTextSplitter 封装
#
#  功能：
#    - 将 Document 列表按 chunk_size 切分为更小的块
#    - 参数从 config_loader 读取（chunk_size / chunk_overlap / separator）
#    - 保持 metadata 传递，便于后续溯源
#
#  使用方式：
#    from core.text_splitter import split_documents
#    chunks = split_documents(docs)  # 参数自动从配置读取
# =========================================
import logging
from typing import List, Optional

from core.config_loader import settings
from core.document_parser import Document

# 日志
_logger = logging.getLogger(__name__)


# ============================================================
# 尝试导入 LangChain 的 RecursiveCharacterTextSplitter
# ============================================================
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        # 兼容旧版本 langchain
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        _LANGCHAIN_AVAILABLE = True
    except ImportError:
        _LANGCHAIN_AVAILABLE = False
        _logger.warning(
            "⚠️  未安装 langchain-text-splitters，将使用简易分块实现。\n"
            "   建议执行：pip install langchain-text-splitters"
        )


# ============================================================
# 核心分块函数
# ============================================================
def split_documents(
    docs: List[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    separator: Optional[str] = None,
) -> List[Document]:
    """
    将 Document 列表分块为更小的 Document 列表。

    参数：
        docs: 待分块的 Document 列表（来自 document_parser）
        chunk_size: 每块字符数（默认从 settings.splitter.chunk_size 读取）
        chunk_overlap: 块间重叠字符数（默认从 settings.splitter.chunk_overlap 读取）
        separator: 分块优先分隔符（默认从 settings.splitter.separator 读取）

    返回：
        List[Document]: 分块后的 Document 列表，每个块携带原 metadata + part 信息
    """
    # 1) 参数读取（优先使用传入参数，否则从配置读取）
    _chunk_size = chunk_size or settings.splitter.chunk_size
    _chunk_overlap = chunk_overlap or settings.splitter.chunk_overlap
    _separator = separator or settings.splitter.separator

    # 2) 参数校验
    if _chunk_size <= 0:
        raise ValueError(f"chunk_size 必须大于 0，当前值：{_chunk_size}")
    if _chunk_overlap < 0:
        raise ValueError(f"chunk_overlap 不能为负数，当前值：{_chunk_overlap}")
    if _chunk_overlap >= _chunk_size:
        raise ValueError(
            f"chunk_overlap 必须小于 chunk_size，当前：overlap={_chunk_overlap}, size={_chunk_size}"
        )

    # 3) 空输入直接返回
    if not docs:
        _logger.warning("输入 Document 列表为空，返回空列表")
        return []

    # 4) 统计输入
    total_chars = sum(len(d.page_content) for d in docs)
    _logger.info(
        "开始分块：输入 %d 个 Document，总字符数 %d，chunk_size=%d, overlap=%d",
        len(docs), total_chars, _chunk_size, _chunk_overlap
    )

    # 5) 分块处理
    chunks: List[Document] = []

    if _LANGCHAIN_AVAILABLE:
        # ----- 使用 LangChain RecursiveCharacterTextSplitter -----
        # 构造 splitter（ separators 按优先级尝试分割）
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=_chunk_size,
            chunk_overlap=_chunk_overlap,
            separators=[
                _separator,      # 用户配置的优先分隔符（如 "\n"）
                "\n\n",          # 段落分隔
                "\n",            # 行分隔
                "。",            # 中文句号
                "；",            # 中文分号
                "，",            # 中文逗号
                " ",             # 空格
                "",              # 最后按字符切
            ],
            length_function=len,
            is_separator_regex=False,
        )

        # 逐个 Document 分块
        for doc_idx, doc in enumerate(docs):
            text = doc.page_content
            if not text or not text.strip():
                continue

            # 调用 LangChain splitter
            try:
                langchain_chunks = splitter.split_text(text)
            except Exception as e:
                _logger.warning(
                    "LangChain 分块失败（%s），使用简易实现：Document %d",
                    str(e), doc_idx
                )
                langchain_chunks = _simple_split(text, _chunk_size, _chunk_overlap)

            # 转换为 Document 对象，保留 metadata
            for part_idx, chunk_text in enumerate(langchain_chunks):
                if not chunk_text.strip():
                    continue

                # 复制原 metadata，添加分块信息
                chunk_meta = dict(doc.metadata)
                chunk_meta["chunk_index"] = part_idx
                chunk_meta["chunk_total"] = len(langchain_chunks)
                chunk_meta["chunk_size"] = len(chunk_text)
                chunk_meta["source_doc_index"] = doc_idx

                chunks.append(Document(chunk_text, chunk_meta))

    else:
        # ----- 简易实现（LangChain 未安装时）-----
        for doc_idx, doc in enumerate(docs):
            text = doc.page_content
            if not text or not text.strip():
                continue

            simple_chunks = _simple_split(text, _chunk_size, _chunk_overlap)

            for part_idx, chunk_text in enumerate(simple_chunks):
                if not chunk_text.strip():
                    continue

                chunk_meta = dict(doc.metadata)
                chunk_meta["chunk_index"] = part_idx
                chunk_meta["chunk_total"] = len(simple_chunks)
                chunk_meta["chunk_size"] = len(chunk_text)
                chunk_meta["source_doc_index"] = doc_idx

                chunks.append(Document(chunk_text, chunk_meta))

    # 6) 统计输出
    _logger.info(
        "分块完成：输出 %d 个 chunk，总字符数 %d",
        len(chunks), sum(len(c.page_content) for c in chunks)
    )

    return chunks


# ============================================================
# 简易分块实现（LangChain 未安装时的备用方案）
# ============================================================
def _simple_split(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> List[str]:
    """
    简易按字符数分块（不依赖 LangChain）。

    参数：
        text: 待分块文本
        chunk_size: 每块字符数
        chunk_overlap: 块间重叠字符数

    返回：
        List[str]: 分块后的文本列表
    """
    if not text:
        return []

    chunks: List[str] = []
    step = chunk_size - chunk_overlap
    length = len(text)
    idx = 0

    while idx < length:
        chunk = text[idx: idx + chunk_size]
        chunks.append(chunk)
        idx += step

    return chunks


# ============================================================
# 工具函数：预估分块数量
# ============================================================
def estimate_chunk_count(
    docs: List[Document],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> int:
    """
    预估分块后的 Document 数量（用于 UI 提示）。

    公式：总字符数 / (chunk_size - chunk_overlap) * 安全系数
    """
    _chunk_size = chunk_size or settings.splitter.chunk_size
    _chunk_overlap = chunk_overlap or settings.splitter.chunk_overlap

    if _chunk_size <= _chunk_overlap:
        return 0

    total_chars = sum(len(d.page_content) for d in docs)
    step = _chunk_size - _chunk_overlap

    # 预估（考虑重叠带来的额外块）
    estimated = int(total_chars / step) + len(docs)  # 每个 doc 至少 1 块
    return estimated


# ============================================================
# 导出
# ============================================================
__all__ = [
    "split_documents",
    "estimate_chunk_count",
]


# ============================================================
# 直接运行本文件时的调试输出
# 用法：python -m core.text_splitter
# ============================================================
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # 测试：对指定文本进行分块
    test_text = """
这是一段测试文本，用于验证文本分块功能。

RecursiveCharacterTextSplitter 会按照分隔符优先级进行分块，
优先使用段落分隔符，然后是行分隔符，最后是字符切分。

这样可以尽量保持语义完整性，避免把一句话切成两半。

本模块支持从配置文件读取分块参数，便于统一管理。
"""

    # 构造测试 Document
    test_doc = Document(test_text, {"source": "test", "filename": "test.txt"})
    docs = [test_doc]

    # 分块
    chunks = split_documents(docs)

    print(f"\n输入：1 个 Document，{len(test_text)} 字符")
    print(f"输出：{len(chunks)} 个 chunk")
    print(f"配置：chunk_size={settings.splitter.chunk_size}, overlap={settings.splitter.chunk_overlap}")

    for i, chunk in enumerate(chunks):
        print(f"\n[Chunk {i+1}] 长度={len(chunk.page_content)}")
        print(chunk.page_content[:100] + "..." if len(chunk.page_content) > 100 else chunk.page_content)
        print(f"元数据：{chunk.metadata}")