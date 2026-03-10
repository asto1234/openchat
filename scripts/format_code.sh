#!/bin/bash
# Code formatting script for OpenChat

set -e

echo "Code Formatting for OpenChat"
echo "============================"

# Check if tools are installed
for tool in black isort; do
    if ! command -v $tool &> /dev/null; then
        echo "ERROR: $tool is not installed"
        echo "Install with: pip install black isort"
        exit 1
    fi
done

# Format with isort (import sorting)
echo "Sorting imports with isort..."
isort openchat tests examples --profile black

# Format with black
echo "Formatting code with black..."
black openchat tests examples --line-length 100

echo ""
echo "Code formatting complete!"
