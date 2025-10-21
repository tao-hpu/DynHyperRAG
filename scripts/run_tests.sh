#!/bin/bash

# Test Runner Script for HyperGraphRAG Visualization API
# This script runs all test suites with proper configuration

set -e  # Exit on error

echo "========================================="
echo "HyperGraphRAG Visualization API Tests"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create a .env file with required configuration"
    exit 1
fi

# Check if example data exists
if [ ! -d expr/example ]; then
    echo -e "${RED}Error: Example data directory not found${NC}"
    echo "Please ensure expr/example/ directory exists with test data"
    exit 1
fi

# Function to run tests with error handling
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "Command: $test_command"
    echo ""
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        echo ""
        return 1
    fi
}

# Track test results
total_tests=0
passed_tests=0
failed_tests=0

# Test 1: Model Unit Tests (Fast)
total_tests=$((total_tests + 1))
if run_test "Model Unit Tests" "python -m pytest tests/test_models.py -v --tb=short"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
fi

# Test 2: API Integration Tests
total_tests=$((total_tests + 1))
echo -e "${YELLOW}Note: Integration tests require API initialization and may take longer${NC}"
if run_test "API Integration Tests" "python -m pytest tests/test_api_integration.py -v --tb=short -x"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
    echo -e "${YELLOW}Integration tests failed. This may be due to:${NC}"
    echo "  - Missing dependencies (run: pip install -r requirements.txt)"
    echo "  - Invalid API keys in .env file"
    echo "  - Missing or corrupted test data in expr/example/"
fi

# Test 3: Performance Tests
total_tests=$((total_tests + 1))
echo -e "${YELLOW}Note: Performance tests include timing assertions and LLM API calls${NC}"
if run_test "Performance Tests" "python -m pytest tests/test_performance.py -v --tb=short -s"; then
    passed_tests=$((passed_tests + 1))
else
    failed_tests=$((failed_tests + 1))
    echo -e "${YELLOW}Performance tests failed. This may be due to:${NC}"
    echo "  - System load affecting response times"
    echo "  - Network latency to LLM API"
    echo "  - Timeout values may need adjustment for your environment"
fi

# Summary
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Total test suites: $total_tests"
echo -e "${GREEN}Passed: $passed_tests${NC}"
if [ $failed_tests -gt 0 ]; then
    echo -e "${RED}Failed: $failed_tests${NC}"
else
    echo -e "Failed: $failed_tests"
fi
echo ""

if [ $failed_tests -eq 0 ]; then
    echo -e "${GREEN}All test suites passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some test suites failed${NC}"
    echo "See output above for details"
    exit 1
fi
