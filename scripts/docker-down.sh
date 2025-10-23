#!/bin/bash

# Docker shutdown script for HyperGraphRAG Visualization
# This script stops and removes Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping HyperGraphRAG Docker services${NC}"
echo ""

# Parse command line arguments
REMOVE_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes|-v)
            REMOVE_VOLUMES=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--volumes]"
            exit 1
            ;;
    esac
done

# Stop production services
if docker-compose ps | grep -q "hypergraphrag"; then
    echo -e "${YELLOW}Stopping production services...${NC}"
    if [ "$REMOVE_VOLUMES" = true ]; then
        docker-compose down -v
    else
        docker-compose down
    fi
fi

# Stop development services
if docker-compose -f docker-compose.dev.yml ps | grep -q "hypergraphrag"; then
    echo -e "${YELLOW}Stopping development services...${NC}"
    if [ "$REMOVE_VOLUMES" = true ]; then
        docker-compose -f docker-compose.dev.yml down -v
    else
        docker-compose -f docker-compose.dev.yml down
    fi
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${YELLOW}⚠️  Volumes removed${NC}"
fi
