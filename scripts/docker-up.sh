#!/bin/bash

# Docker startup script for HyperGraphRAG Visualization
# This script starts the application using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 Starting HyperGraphRAG with Docker Compose${NC}"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.docker...${NC}"
    cp .env.docker .env
    echo -e "${RED}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Parse command line arguments
MODE="production"
DETACHED="-d"

while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            MODE="development"
            shift
            ;;
        --foreground|-f)
            DETACHED=""
            shift
            ;;
        --build)
            echo -e "${BLUE}🏗️  Building images first...${NC}"
            ./scripts/build.sh
            echo ""
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--dev] [--foreground] [--build]"
            exit 1
            ;;
    esac
done

# Select compose file
if [ "$MODE" = "development" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    echo -e "${YELLOW}📝 Using development configuration${NC}"
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "${BLUE}📝 Using production configuration${NC}"
fi

# Start services
echo -e "${GREEN}🚀 Starting services...${NC}"
docker-compose -f $COMPOSE_FILE up $DETACHED

if [ -n "$DETACHED" ]; then
    # Wait for services to be healthy
    echo ""
    echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
    sleep 5
    
    # Check backend health
    for i in {1..30}; do
        if curl -s http://localhost:3401/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend health check timeout${NC}"
            docker-compose -f $COMPOSE_FILE logs backend
            exit 1
        fi
        sleep 1
    done
    
    # Check frontend health
    for i in {1..30}; do
        if curl -s http://localhost:80/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Frontend health check timeout${NC}"
            docker-compose -f $COMPOSE_FILE logs frontend
            exit 1
        fi
        sleep 1
    done
    
    echo ""
    echo -e "${GREEN}✅ All services are running!${NC}"
    echo ""
    echo -e "📍 Frontend UI:  ${GREEN}http://localhost${NC}"
    echo -e "📍 Backend API:  ${GREEN}http://localhost:3401${NC}"
    echo -e "📍 API Docs:     ${GREEN}http://localhost:3401/docs${NC}"
    echo ""
    echo -e "📝 View logs:    ${BLUE}docker-compose -f $COMPOSE_FILE logs -f${NC}"
    echo -e "🛑 Stop:         ${BLUE}docker-compose -f $COMPOSE_FILE down${NC}"
fi
