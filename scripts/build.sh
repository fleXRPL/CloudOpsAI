#!/bin/bash
set -e

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/
mkdir -p dist/

# Create Lambda layer with runtime dependencies
echo "Building Lambda layer..."
mkdir -p layer/python
if ! pip install -r requirements.txt --target ./layer/python; then
    handle_error "Failed to install runtime dependencies"
fi

# Create Lambda layer package
cd layer
if ! zip -r ../dist/lambda-layer.zip python/; then
    handle_error "Failed to create Lambda layer package"
fi
cd ..

# Build Lambda function
echo "Building Lambda function..."
if ! zip -r dist/function.zip ai_noc/; then
    handle_error "Failed to create Lambda function package"
fi

echo "Build completed! Artifacts in dist/"
echo "- Lambda layer: dist/lambda-layer.zip"
echo "- Lambda function: dist/function.zip"
