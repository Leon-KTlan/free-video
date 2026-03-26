#!/bin/bash
# 复制下面这段命令，粘贴到你的系统终端（iTerm/Terminal.app）运行
# ============================================================

cd /Users/leon/Desktop/Code/爬虫/beginner/pythonProject/free-video

# 停止占用 8000 端口的旧进程
kill $(lsof -ti:8000) 2>/dev/null; sleep 1

# 启动后端（新代码，支持代理自动检测）
venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload
