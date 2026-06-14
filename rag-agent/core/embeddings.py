"""
向量嵌入模块：
TODO：接入 langchain_community.embeddings / langchain_openai 等实现
"""


class Embeddings:
    """统一的 Embeddings 封装，便于替换模型。"""

    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        raise NotImplementedError("请在 core/embeddings.py 中实现真实 Embeddings 逻辑。")

    def embed_documents(self, texts: list) -> list:
        raise NotImplementedError

    def embed_query(self, text: str) -> list:
        raise NotImplementedError
