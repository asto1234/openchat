#!/bin/bash
# Test running script for OpenChat

set -e

echo "Running Tests for OpenChat"
echo "=========================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "ERROR: pytest is not installed"
    echo "Install with: pip install -e '.[dev]'"
    exit 1
fi

# Default to running all tests
TEST_PATH="${1:-.}"
COVERAGE="${2:--}"

# Build pytest command
PYTEST_CMD="pytest $TEST_PATH -v"

# Add coverage if specified or default
if [ "$COVERAGE" == "--coverage" ] || [ "$TEST_PATH" == "tests/" ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=openchat --cov-report=term-missing --cov-report=html"
fi

echo "Running tests: $PYTEST_CMD"
echo ""

# Run tests
if $PYTEST_CMD; then
    echo ""
    echo "All tests passed!"
    if [ -d "htmlcov" ]; then
        echo "Coverage report: htmlcov/index.html"
    fi
else
    echo ""
    echo "Some tests failed!"
    exit 1
fi
