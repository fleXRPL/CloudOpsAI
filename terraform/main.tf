terraform {
  backend "s3" {
    bucket         = "cloudopsai-terraform-state"
    key            = "cloudopsai/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "cloudopsai-terraform-state-lock"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "CloudOpsAI"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  common_tags = {
    Environment = var.environment
    Project     = "CloudOpsAI"
    ManagedBy   = "Terraform"
  }
  
  name_prefix = "cloudopsai-${var.environment}"
  
  lambda_tags = merge(local.common_tags, {
    Function    = "NOC-Agent"
    Runtime     = "python3.12"
    Owner       = "team-noc"
    AutoManaged = "true"
  })
  
  dynamodb_tags = merge(local.common_tags, {
    Service = "CloudOpsAI"
    Type    = "NoSQL"
  })
}

module "vpc" {
  source = "./modules/vpc"
  
  vpc_cidr           = var.vpc_cidr
  private_subnets    = var.private_subnets
  public_subnets     = var.public_subnets
  availability_zones = var.availability_zones
  environment        = var.environment
  aws_region         = var.aws_region
  tags               = local.common_tags
}

module "kms" {
  source      = "./modules/kms"
  environment = var.environment
  tags        = local.common_tags
}

module "lambda" {
  source = "./modules/lambda"
  
  function_name      = "${local.name_prefix}-noc-agent"
  lambda_role_arn    = module.iam.lambda_role_arn
  vpc_config = {
    subnet_ids         = module.vpc.private_subnet_ids
    security_group_ids = [module.vpc.lambda_security_group_id]
  }
  runtime            = "python3.12"
  config_s3_bucket   = module.s3.bucket_name
  config_s3_key      = "config/remediation_actions.yaml"
  lambda_tags        = local.lambda_tags
  environment        = var.environment
  log_encryption_key = module.kms.cloudwatch_key_arn
}

module "monitoring" {
  source = "./modules/monitoring"
  
  aws_region     = var.aws_region
  environment    = var.environment
  function_name  = module.lambda.function_name
  alarm_actions  = var.alarm_actions
  log_group_name = "/aws/lambda/${module.lambda.function_name}"
  tags           = local.common_tags
}

module "dynamodb" {
  source = "./modules/dynamodb"
  
  table_name = "NOCIncidents"
  tags       = local.dynamodb_tags
}

module "s3" {
  source = "./modules/s3"
  
  bucket_name = var.config_bucket_name
  tags        = local.common_tags
}

module "iam" {
  source = "./modules/iam"
  
  function_name    = local.name_prefix
  config_s3_bucket = module.s3.bucket_name
  kms_key_arn      = module.kms.key_arn
  tags             = local.common_tags
}
