# =========================================
#  RAG 知识库 Agent - 启动入口
#  端口：8000，运行平台：Windows
#  运行方式：python main.py  或  run.bat
# =========================================
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_app_settings
from api.v1.health_router import router as health_router
from api.v1.kb_router import router as kb_router
from api.v1.qa_router import router as qa_router
from utils.logger import setup_logger

# 1) 读取全局配置
settings = get_app_settings()

# 2) 初始化日志
setup_logger(log_dir=settings.paths.logs, level=settings.server.log_level)

# 3) host / port
HOST = settings.server.host
PORT = settings.server.port

# 4) 构建 FastAPI 实例
app = FastAPI(
    title="CZJ RAG 知识库 Agent",
    description="个人自用的 RAG 问答服务，供 Java 系统调用。",
    version="0.1.0",
)

# 5) 配置 CORS（为 Java 前端 / Java 服务跨域调用预留）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # 生产环境可改为具体域名，如 ["http://localhost:8080"]
    allow_credentials=True,          # 允许携带 Cookie / Authorization
    allow_methods=["*"],            # 允许所有 HTTP 方法
    allow_headers=["*"],           # 允许所有请求头
)

# 6) 挂载路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(qa_router, prefix="/api/v1")


# ---------- 根路径 ----------
@app.get("/", tags=["根路径"])
def root():
    """服务概览（调试用）。"""
    return {
        "service": "czj-kb-agent",
        "host": HOST,
        "port": PORT,
        "llm": f"{settings.llm.provider} / {settings.llm.model}",
        "api_key_ok": bool(settings.llm.api_key),
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ---------- 启动 ----------
if __name__ == "__main__":
    print(settings.summary())
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        reload=False,   # Windows 个人使用，关闭 reload 避免文件监听问题
    )
