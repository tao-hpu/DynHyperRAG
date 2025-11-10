#!/bin/bash

# HyperGraphRAG 服务启动脚本

echo "🚀 启动 HyperGraphRAG 服务..."

# 检查端口占用
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# 启动后端 API
echo ""
echo "📡 启动后端 API (端口 3401)..."
if check_port 3401; then
    echo "⚠️  端口 3401 已被占用，尝试停止旧进程..."
    pkill -f "uvicorn api.main:app"
    sleep 2
fi

uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload &
API_PID=$!
echo "✅ 后端 API 已启动 (PID: $API_PID)"

# 等待后端启动
sleep 3

# 启动前端
echo ""
echo "🎨 启动前端 Web UI (端口 3400)..."
cd web_ui

if check_port 3400; then
    echo "⚠️  端口 3400 已被占用，尝试停止旧进程..."
    pkill -f "pnpm dev"
    sleep 2
fi

pnpm dev

# 注意：前端会在前台运行，按 Ctrl+C 停止
# 停止时会自动清理后端进程
trap "echo ''; echo '🛑 停止服务...'; kill $API_PID 2>/dev/null; exit" INT TERM
