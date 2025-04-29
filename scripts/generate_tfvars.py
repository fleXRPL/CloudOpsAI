#!/usr/bin/env python3
"""
Generate Terraform variables from YAML configuration.
"""

import os
import sys
import yaml
import json
from pathlib import Path

def load_config(config_path: str) -> dict:
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)

def generate_tfvars(config: dict) -> str:
    """Generate Terraform variables file content."""
    # Extract variables from config
    aws_region = config['aws']['region']
    environment = config['aws']['environment']
    project_name = config['project']['name']
    function_name = config['project']['function_name']
    config_bucket_name = config['project']['config_bucket_name']
    
    # Network configuration
    vpc_cidr = config['network']['vpc']['cidr']
    public_subnets = config['network']['vpc']['public_subnets']
    private_subnets = config['network']['vpc']['private_subnets']
    availability_zones = config['network']['vpc']['availability_zones']
    
    # Notification configuration
    alarm_actions = config['notifications']['alarm_actions']
    
    # AWS Account configuration
    primary_account = config['aws']['accounts']['primary']
    target_accounts = config['aws']['accounts']['targets']
    
    # Monitoring configuration
    monitoring = config['monitoring']
    
    # Generate tfvars content
    tfvars = f"""# Generated from config/terraform.yaml
aws_region = "{aws_region}"
environment = "{environment}"
project = "{project_name}"
function_name = "{function_name}"
config_bucket_name = "{config_bucket_name}"
vpc_cidr = "{vpc_cidr}"
public_subnets = {json.dumps(public_subnets)}
private_subnets = {json.dumps(private_subnets)}
availability_zones = {json.dumps(availability_zones)}
alarm_actions = {json.dumps(alarm_actions)}

# AWS Account Configuration
primary_account = {{
  id     = "{primary_account['id']}"
  role   = "{primary_account['role']}"
  profile = "{primary_account['profile']}"
}}

target_accounts = {json.dumps(target_accounts)}

# Monitoring Configuration
monitoring = {{
  cross_account     = {str(monitoring['cross_account']).lower()}
  centralized_logging = {str(monitoring['centralized_logging']).lower()}
  log_retention_days = {monitoring['log_retention_days']}
  metrics_retention_days = {monitoring['metrics_retention_days']}
  dashboard_enabled = {str(monitoring['dashboard_enabled']).lower()}
}}
"""
    return tfvars

def main():
    """Main entry point."""
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Load configuration
    config_path = project_root / 'config' / 'terraform.yaml'
    config = load_config(config_path)
    
    # Generate tfvars
    tfvars_content = generate_tfvars(config)
    
    # Write to terraform.tfvars
    tfvars_path = project_root / 'terraform' / 'terraform.tfvars'
    with open(tfvars_path, 'w') as f:
        f.write(tfvars_content)
    
    print(f"Generated {tfvars_path}")

if __name__ == '__main__':
    main() 