# =========================================
#  RAG 知识库 Agent - 启动入口
#  端口：8000，运行平台：Windows
#  运行方式：python main.py  或  run.bat
# =========================================
import uvicorn
from fastapi import FastAPI

from api.deps import get_app_settings
from api.v1.health_router import router as health_router
from api.v1.kb_router import router as kb_router
from api.v1.qa_router import router as qa_router
from utils.logger import setup_logger

# 1) 读取全局配置（Settings 对象，由 core/config_loader.py 提供）
settings = get_app_settings()

# 2) 初始化日志（传入配置中的日志目录与级别）
setup_logger(log_dir=settings.paths.logs, level=settings.server.log_level)

# 3) host / port 读取自 settings.yaml（port 默认 8000）
HOST = settings.server.host
PORT = settings.server.port

# 4) 构建 FastAPI 应用
app = FastAPI(
    title="CZJ RAG 知识库 Agent",
    description="个人自用的 RAG 问答服务，供 Java 系统调用。",
    version="0.1.0",
)

# 5) 挂载路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(qa_router, prefix="/api/v1")


# ---------- 调试用的根路径 ----------
@app.get("/", tags=["根路径"])
def root():
    return {
        "service": "czj-kb-agent",
        "host": HOST,
        "port": PORT,
        "llm": f"{settings.llm.provider} / {settings.llm.model}",
        "api_key_ok": bool(settings.llm.api_key),
        "docs": "/docs",
    }


# ---------- 启动 ----------
if __name__ == "__main__":
    # 打印启动日志
    print(settings.summary())
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
