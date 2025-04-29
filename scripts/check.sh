#!/bin/bash
set -e

echo "================================================"
echo "Running all code quality checks..."
echo "================================================"

# Ensure we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "Error: No virtual environment found. Please run 'source scripts/init.sh' first."
        exit 1
    fi
fi

# Install dependencies if needed
if ! pip show mypy > /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "Running code quality checks..."

# Run black formatter
echo "Running Black formatter..."
black ai_noc/ tests/

# Run import sort
echo "Running import sort..."
isort ai_noc/ tests/

# Run flake8
echo "Running Flake8 linter..."
flake8 ai_noc/ tests/ || exit 1

# Run mypy type checker
echo "Running MyPy type checker..."
mypy ai_noc/ || exit 1

echo "All checks completed successfully!" 