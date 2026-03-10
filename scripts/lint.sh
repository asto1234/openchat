#!/bin/bash
# Code linting script for OpenChat

set -e

echo "Code Linting for OpenChat"
echo "=========================="

FAILED=0

# Check if tools are installed
for tool in ruff mypy flake8; do
    if ! command -v $tool &> /dev/null; then
        echo "WARNING: $tool is not installed"
        echo "Install with: pip install ruff mypy flake8"
    fi
done

# Run ruff checks
echo ""
echo "Running ruff checks..."
if command -v ruff &> /dev/null; then
    if ! ruff check openchat tests examples; then
        FAILED=1
    fi
else
    echo "SKIPPED: ruff not installed"
fi

# Run type checking with mypy
echo ""
echo "Running type checks with mypy..."
if command -v mypy &> /dev/null; then
    if ! mypy openchat; then
        FAILED=1
    fi
else
    echo "SKIPPED: mypy not installed"
fi

# Run flake8 checks
echo ""
echo "Running flake8 checks..."
if command -v flake8 &> /dev/null; then
    if ! flake8 openchat tests examples --max-line-length=100 --extend-ignore=E203; then
        FAILED=1
    fi
else
    echo "SKIPPED: flake8 not installed"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "All linting checks passed!"
else
    echo "Some linting checks failed!"
    exit 1
fi
