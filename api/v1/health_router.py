# =========================================
#  健康检查路由：GET /api/v1/health
#  供 Java 服务探活使用
# =========================================
import time

from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
def health_check():
    """服务健康检查。"""
    return {
        "status": "ok",
        "service": "czj-kb-agent",
        "timestamp": int(time.time()),
    }
