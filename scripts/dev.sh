#!/bin/bash

# Development startup script for HyperGraphRAG Visualization
# This script starts both backend and frontend in development mode

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting HyperGraphRAG Development Environment${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
    exit 1
fi

# Check if Python dependencies are installed
echo -e "${GREEN}📦 Checking Python dependencies...${NC}"
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if Node.js dependencies are installed
echo -e "${GREEN}📦 Checking Node.js dependencies...${NC}"
if [ ! -d "web_ui/node_modules" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies with pnpm...${NC}"
    cd web_ui
    pnpm install
    cd ..
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend API
echo -e "${GREEN}🔧 Starting Backend API on port 3401...${NC}"
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 3401 --reload > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:3401/api/health > /dev/null; then
    echo -e "${RED}❌ Backend failed to start. Check logs/backend.log${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ Backend API started successfully${NC}"

# Start frontend
echo -e "${GREEN}🎨 Starting Frontend on port 3400...${NC}"
cd web_ui
pnpm dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

echo ""
echo -e "${GREEN}✅ Development environment is ready!${NC}"
echo ""
echo -e "📍 Backend API:  ${GREEN}http://localhost:3401${NC}"
echo -e "📍 API Docs:     ${GREEN}http://localhost:3401/docs${NC}"
echo -e "📍 Frontend UI:  ${GREEN}http://localhost:3400${NC}"
echo ""
echo -e "📝 Logs:"
echo -e "   Backend:  logs/backend.log"
echo -e "   Frontend: logs/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
