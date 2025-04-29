#!/bin/bash

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Error: This script must be sourced. Please run:"
    echo "    source scripts/init.sh"
    echo "or:"
    echo "    . scripts/init.sh"
    exit 1
fi

echo "Setting up CloudOpsAI development environment..."

# Check Python version
if ! command -v python3 &>/dev/null; then
    echo "Error: Python 3 is required but not found"
    return 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo "Warning: AWS credentials not configured. Some features may not work."
    echo "Run 'aws configure' to set up credentials."
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    return 1
fi

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Make scripts executable
chmod +x scripts/*.sh

echo "================================================"
echo "CloudOpsAI development environment is ready!"
echo "================================================"
echo "Virtual environment is now active: $VIRTUAL_ENV"
echo ""
echo "Available commands:"
echo "- ./scripts/check.sh   : Run all code quality checks"
echo "- ./scripts/build.sh   : Build packages"
echo "- ./scripts/deploy.sh  : Deploy to AWS"
echo ""
echo "To deactivate the virtual environment later, run: deactivate"
echo "================================================"
