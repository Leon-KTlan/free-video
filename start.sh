#!/bin/bash
# =================================================
# VideoSnap 一键启动脚本
# 使用方法：在 iTerm/Terminal.app 中运行此脚本
# 不要在 Cursor 内置终端运行！
# =================================================

PROJECT="/Users/leon/Desktop/Code/爬虫/beginner/pythonProject/free-video"

echo ""
echo "========================================"
echo "   VideoSnap 万能视频下载器"
echo "========================================"

# 停止占用端口的旧进程
for port in 8000 8001 5173 5174; do
  pid=$(lsof -ti:$port 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "停止端口 $port 上的进程 PID=$pid"
    kill -9 $pid 2>/dev/null
  fi
done
sleep 1

# 启动后端（端口 8000）
echo ""
echo "[1/2] 启动后端服务..."
cd "$PROJECT"
"$PROJECT/venv/bin/uvicorn" app:app --host 0.0.0.0 --port 8000 --reload > /tmp/videosnap_backend.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端就绪
for i in {1..10}; do
  if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "后端启动成功 ✓ (http://localhost:8000)"
    break
  fi
  sleep 1
done

# 启动前端（端口 5173）
echo ""
echo "[2/2] 启动前端服务..."
cd "$PROJECT/frontend"
npm run dev > /tmp/videosnap_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"
sleep 3

# 获取本机IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "未知")

echo ""
echo "========================================"
echo "  ✓ 启动完成！"
echo "----------------------------------------"
echo "  电脑访问: http://localhost:5173"
echo "  手机访问: http://$LOCAL_IP:5173"
echo "  后端API:  http://localhost:8000"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '已停止'; exit 0" INT TERM
wait
