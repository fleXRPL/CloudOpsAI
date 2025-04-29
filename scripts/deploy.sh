#!/bin/bash
set -e

# Function to handle errors
handle_error() {
    echo "Error: $1"
    exit 1
}

# Function to check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &>/dev/null; then
        handle_error "AWS credentials not configured. Please run 'aws configure' first."
    fi
}

# Function to check configuration
check_configuration() {
    if [ ! -f "config/terraform.yaml" ]; then
        handle_error "Configuration file config/terraform.yaml not found. Please create it first."
    fi
    
    # Check if Python is available
    if ! command -v python3 &>/dev/null; then
        handle_error "Python 3 is required but not found."
    fi
    
    # Check if required Python packages are installed
    if ! python3 -c "import yaml" &>/dev/null; then
        echo "Installing required Python packages..."
        pip install pyyaml
    fi
}

# Function to initialize Terraform state
init_terraform_state() {
    echo "Initializing Terraform state..."
    cd terraform/state-bucket
    if ! terraform init; then
        handle_error "Failed to initialize Terraform state"
    fi
    if ! terraform apply -auto-approve; then
        handle_error "Failed to create Terraform state infrastructure"
    fi
    cd ../..
}

# Check AWS credentials
check_aws_credentials

# Check configuration
check_configuration

# Build packages
echo "Building packages..."
if ! ./scripts/build.sh; then
    handle_error "Build failed"
fi

# Run tests
echo "Running tests..."
if ! ./scripts/check.sh; then
    handle_error "Tests failed"
fi

# Generate Terraform variables
echo "Generating Terraform variables..."
if ! python3 scripts/generate_tfvars.py; then
    handle_error "Failed to generate Terraform variables"
fi

# Initialize Terraform state if needed
if [ ! -f "terraform/state-bucket/terraform.tfstate" ]; then
    init_terraform_state
fi

# Deploy infrastructure
echo "Deploying infrastructure..."
cd terraform
if ! terraform init; then
    handle_error "Failed to initialize Terraform"
fi
if ! terraform plan; then
    handle_error "Failed to create Terraform plan"
fi
if ! terraform apply -auto-approve; then
    handle_error "Failed to apply Terraform changes"
fi
cd ..

echo "Deployment completed successfully!"
