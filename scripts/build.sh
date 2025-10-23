#!/bin/bash

# Build script for HyperGraphRAG Visualization
# This script builds Docker images for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏗️  Building HyperGraphRAG Docker Images${NC}"
echo ""

# Parse command line arguments
BUILD_BACKEND=true
BUILD_FRONTEND=true
NO_CACHE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BUILD_FRONTEND=false
            shift
            ;;
        --frontend-only)
            BUILD_BACKEND=false
            shift
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--backend-only] [--frontend-only] [--no-cache]"
            exit 1
            ;;
    esac
done

# Get version from git tag or use 'latest'
VERSION=$(git describe --tags --always 2>/dev/null || echo "latest")
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo ""

# Build backend
if [ "$BUILD_BACKEND" = true ]; then
    echo -e "${GREEN}🔧 Building Backend API image...${NC}"
    docker build $NO_CACHE \
        -t hypergraphrag-api:${VERSION} \
        -t hypergraphrag-api:latest \
        -f api/Dockerfile \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend image built successfully${NC}"
    else
        echo -e "${RED}❌ Backend build failed${NC}"
        exit 1
    fi
    echo ""
fi

# Build frontend
if [ "$BUILD_FRONTEND" = true ]; then
    echo -e "${GREEN}🎨 Building Frontend UI image...${NC}"
    docker build $NO_CACHE \
        -t hypergraphrag-web:${VERSION} \
        -t hypergraphrag-web:latest \
        -f web_ui/Dockerfile \
        web_ui/
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend image built successfully${NC}"
    else
        echo -e "${RED}❌ Frontend build failed${NC}"
        exit 1
    fi
    echo ""
fi

# Show built images
echo -e "${GREEN}📦 Built Images:${NC}"
docker images | grep hypergraphrag | head -n 4

echo ""
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Copy .env.docker to .env and configure"
echo -e "  2. Run: ${BLUE}docker-compose up -d${NC}"
echo -e "  3. Access UI at: ${BLUE}http://localhost${NC}"
