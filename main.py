# =========================================
#  RAG 知识库 Agent - 启动入口
#  端口：8000，运行平台：Windows
#  运行方式：python main.py  或  run.bat
# =========================================
import uvicorn
from fastapi import FastAPI

from api.deps import get_settings
from api.v1.health_router import router as health_router
from api.v1.kb_router import router as kb_router
from api.v1.qa_router import router as qa_router
from utils.logger import setup_logger

# 初始化日志
setup_logger()

# 加载配置（端口固定：8000，在 config/settings.yaml 中维护）
settings = get_settings()
HOST = settings.get("server", {}).get("host", "0.0.0.0")
PORT = int(settings.get("server", {}).get("port", 8000))

# 构建 FastAPI 应用
app = FastAPI(
    title="CZJ RAG 知识库 Agent",
    description="个人自用的 RAG 问答服务，供 Java 系统调用。",
    version="0.1.0",
)

# 挂载路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(qa_router, prefix="/api/v1")


@app.get("/", tags=["根路径"])
def root():
    return {
        "service": "czj-kb-agent",
        "port": PORT,
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
