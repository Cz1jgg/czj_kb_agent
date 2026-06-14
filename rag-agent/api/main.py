"""
API 主入口：FastAPI 应用初始化，统一路由管理
启动命令：uvicorn api.main:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.routes.documents import router as documents_router
from api.routes.vectorstore import router as vectorstore_router
from api.routes.qa import router as qa_router

# 初始化 FastAPI
app = FastAPI(
    title="RAG-Agent",
    description="个人 RAG 知识库 Agent 接口",
    version="0.1.0",
)

# 统一路由管理
app.include_router(documents_router)
app.include_router(vectorstore_router)
app.include_router(qa_router)


@app.get("/", summary="健康检查", tags=["系统"])
async def root():
    """健康检查接口，供 Java 服务探活。"""
    return JSONResponse(content={"status": "ok", "service": "rag-agent", "port": 8000})


@app.get("/health", summary="健康检查", tags=["系统"])
async def health():
    return {"status": "ok"}
