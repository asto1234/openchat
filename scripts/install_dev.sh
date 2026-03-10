#!/bin/bash
# Development environment setup script for OpenChat

set -e

echo "=========================================="
echo "OpenChat Development Setup"
echo "=========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

echo "Python version: $PYTHON_VERSION"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "ERROR: Python 3.11+ is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip, setuptools, and wheel
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install package in editable mode with all dependencies
echo "Installing OpenChat in development mode..."
pip install -e ".[dev,docs,kubernetes]"

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "Setting up pre-commit hooks..."
    pre-commit install
else
    echo "Installing pre-commit..."
    pip install pre-commit
    pre-commit install
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest tests/"
echo ""
echo "To run with coverage:"
echo "  pytest tests/ --cov=openchat --cov-report=html"
echo ""
echo "To run benchmarks:"
echo "  pytest benchmarks/ -v"
echo ""
echo "To format code:"
echo "  black openchat tests examples"
echo "  isort openchat tests examples"
echo ""
echo "To lint code:"
echo "  ruff check openchat tests examples"
echo ""
echo "To check types:"
echo "  mypy openchat"
echo ""
