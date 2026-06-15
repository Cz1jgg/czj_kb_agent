# =========================================
#  通义千问 Embedding 自定义实现
#  解决 OpenAIEmbeddings 与通义接口不兼容的问题
#  接口文档：https://help.aliyun.com/zh/model-studio/developer-reference/embeddings-api
# =========================================
import logging
from typing import List
import os
from dotenv import load_dotenv

import requests
from langchain.embeddings.base import Embeddings

# 加载环境变量
load_dotenv()
# 日志
_logger = logging.getLogger(__name__)


class QwenTextEmbedding(Embeddings):
    """
    通义千问 Embedding 模型封装，兼容 LangChain Embeddings 接口。
    
    直接使用 requests 调用通义 OpenAI 兼容接口，避免 OpenAIEmbeddings 的格式问题。
    """

    def __init__(
        self,
        model: str = "text-embedding-v3",
        api_key: str = "",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        timeout: int = 60,
    ):
        """
        初始化 QwenTextEmbedding。

        参数：
            model: 模型名称，默认 text-embedding-v3
            api_key: API Key（优先入参，无则读取环境变量 OPENAI_API_KEY）
            base_url: API 基础地址
            timeout: 请求超时时间（秒）
        """
        self.model = model
        # 优先取传入key，没有则读环境变量
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # 构建完整的 API 路径
        self._api_url = f"{self.base_url}/embeddings"

        if not self.api_key:
            _logger.warning("⚠️ QwenTextEmbedding: API Key 未配置")

    def _request_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        调用通义 Embedding API 获取向量。

        参数：
            texts: 文本列表

        返回：
            向量列表，每个文本对应一个向量
        """
        if not texts:
            return []

        try:
            # 修正鉴权头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": self.model,
                "input": texts,
            }

            response = requests.post(
                self._api_url,
                headers=headers,
                json=data,
                timeout=self.timeout,
            )

            response.raise_for_status()
            result = response.json()

            # 解析响应
            if "data" in result:
                # 按索引排序确保顺序一致
                embeddings = sorted(
                    result["data"],
                    key=lambda x: x["index"]
                )
                return [item["embedding"] for item in embeddings]
            else:
                _logger.error("❌ Embedding API 返回格式异常：%s", result)
                raise ValueError(f"API 返回格式错误: {result}")

        except requests.exceptions.RequestException as e:
            _logger.error("❌ Embedding API 请求失败：%s", e)
            raise
        except Exception as e:
            _logger.error("❌ Embedding 处理失败：%s", e)
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        对单个查询文本进行向量化。

        参数：
            text: 待向量化的文本

        返回：
            文本对应的向量列表
        """
        text = str(text).strip()
        if not text:
            _logger.warning("⚠️ embed_query: 输入文本为空")
            return []
        
        embeddings = self._request_embeddings([text])
        return embeddings[0] if embeddings else []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        对多个文档文本进行向量化。

        参数：
            texts: 待向量化的文本列表

        返回：
            向量列表，每个元素是一个文本的向量
        """
        # 过滤空文本，保留原始索引映射
        valid_texts = []
        valid_indices = []
        
        for idx, text in enumerate(texts):
            str_text = str(text).strip()
            if str_text:
                valid_texts.append(str_text)
                valid_indices.append(idx)
        
        if not valid_texts:
            _logger.warning("⚠️ embed_documents: 所有输入文本均为空")
            return [[] for _ in texts]
        
        # 调用API获取有效文本的向量
        embeddings = self._request_embeddings(valid_texts)
        
        # 重建结果列表，保持原始顺序
        result = [[] for _ in texts]
        for valid_idx, original_idx in enumerate(valid_indices):
            if valid_idx < len(embeddings):
                result[original_idx] = embeddings[valid_idx]
        
        return result