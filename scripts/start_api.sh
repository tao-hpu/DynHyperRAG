#!/bin/bash
# Start HyperGraphRAG Visualization API

echo "🚀 Starting HyperGraphRAG Visualization API..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating your environment first"
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Please copy .env.example to .env and configure it"
    exit 1
fi

# Check if data directory exists
if [ ! -d "expr/example" ]; then
    echo "⚠️  Warning: expr/example directory not found"
    echo "   Make sure you have run the construction script first"
    echo ""
fi

# Start the API
echo "Starting API on http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python api/main.py
