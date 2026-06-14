@echo off
REM =====================================================
REM  RAG-Agent Windows 启动脚本（固定端口 8000）
REM  先加载 config/.env，再用 uvicorn 启动 FastAPI
REM =====================================================
chcp 65001 >nul
cd /d "%~dp0"

REM 加载环境变量（.env 需与 run.bat 同级或放在 config/）
if exist "config\.env" (
    for /f "usebackq tokens=1,2 delims==" %%G in ("config\.env") do (
        if not "%%H"=="" set "%%G=%%H"
    )
)

echo [RAG-Agent] 启动中，端口 8000 ...
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
