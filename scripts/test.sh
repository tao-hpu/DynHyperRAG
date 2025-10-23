#!/bin/bash

# Test script for HyperGraphRAG Visualization
# This script runs all tests for backend and frontend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Running HyperGraphRAG Tests${NC}"
echo ""

# Parse command line arguments
RUN_BACKEND=true
RUN_FRONTEND=true
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            RUN_FRONTEND=false
            shift
            ;;
        --frontend-only)
            RUN_BACKEND=false
            shift
            ;;
        --verbose|-v)
            VERBOSE="-v"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--backend-only] [--frontend-only] [--verbose]"
            exit 1
            ;;
    esac
done

FAILED=0

# Run backend tests
if [ "$RUN_BACKEND" = true ]; then
    echo -e "${BLUE}🔧 Running Backend Tests...${NC}"
    echo ""
    
    if python3 -m pytest tests/ $VERBOSE --tb=short; then
        echo -e "${GREEN}✅ Backend tests passed${NC}"
    else
        echo -e "${RED}❌ Backend tests failed${NC}"
        FAILED=1
    fi
    echo ""
fi

# Run frontend tests
if [ "$RUN_FRONTEND" = true ]; then
    echo -e "${BLUE}🎨 Running Frontend Tests...${NC}"
    echo ""
    
    cd web_ui
    if pnpm test --run; then
        echo -e "${GREEN}✅ Frontend tests passed${NC}"
    else
        echo -e "${RED}❌ Frontend tests failed${NC}"
        FAILED=1
    fi
    cd ..
    echo ""
fi

# Summary
echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
