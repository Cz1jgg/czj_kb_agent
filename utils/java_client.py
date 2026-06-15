# =========================================
#  Java 服务 HTTP 客户端
#  场景：当本服务需要主动反向调用 Java 服务时使用（如回写问答结果）
#  若仅 Java 调用本服务，则本模块暂不启用
# =========================================
from typing import Any, Dict, Optional

import requests

from utils.logger import get_logger

logger = get_logger(__name__)


class JavaServiceClient:
    """Java 服务 HTTP 客户端（简易封装）。"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    # -------- 通用请求 --------
    def post(self, path: str, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        logger.info(f"POST {url}")
        resp = self.session.post(url, json=json_body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        logger.info(f"GET {url}")
        resp = self.session.get(url, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # -------- 业务级封装（示例，按需实现） --------
    def callback_qa_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """示例：把问答结果回写给 Java 服务。"""
        return self.post("/api/kb/callback/qa", payload)
