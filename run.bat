@echo off
REM =========================================
REM  Windows 一键启动脚本（端口：8000）
REM  双击运行，或在 cmd 中执行：run.bat
REM =========================================

echo [INFO] 激活虚拟环境 venv ...
call venv\Scripts\activate

echo [INFO] 启动 RAG 知识库 Agent，端口 8000 ...
python main.py

pause
