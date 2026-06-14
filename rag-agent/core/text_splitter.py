"""
文本分块模块：
TODO：接入 langchain.text_splitter.RecursiveCharacterTextSplitter
"""
from typing import List


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    对文本进行分块。
    TODO：接入 LangChain 分块器真实实现。
    """
    raise NotImplementedError("请在 core/text_splitter.py 中实现真实分块逻辑。")
