plugin "aws" {
  enabled = true
  version = "0.30.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

config {
  module = true
  force = false
}

# AWS Specific Rules
rule "aws_resource_missing_tags" {
  enabled = true
  tags = ["Environment", "Project", "Owner"]
}

rule "aws_lambda_function_invalid_runtime" {
  enabled = true
}

rule "aws_lambda_function_invalid_handler" {
  enabled = true
}

# Terraform Syntax Rules
rule "terraform_deprecated_syntax" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_typed_variables" {
  enabled = true
}

rule "terraform_naming_convention" {
  enabled = true
  format = "snake_case"
}

rule "terraform_standard_module_structure" {
  enabled = true
}
