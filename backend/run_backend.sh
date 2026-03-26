#!/bin/bash
# 在系统终端（iTerm/Terminal.app）中运行，不要在 Cursor 内置终端运行

PROJECT="/Users/leon/Desktop/Code/爬虫/beginner/pythonProject/free-video"

# 停止占用 8000 端口的旧进程
kill $(lsof -ti:8000) 2>/dev/null; sleep 1

# 启动后端
cd "$PROJECT/backend"
"$PROJECT/venv/bin/uvicorn" app:app --host 0.0.0.0 --port 8000 --reload
