variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "lambda_role_arn" {
  description = "ARN of the IAM role for Lambda execution"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
}

variable "vpc_config" {
  description = "VPC configuration for Lambda"
  type = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
}

variable "config_s3_bucket" {
  description = "S3 bucket containing config files"
  type        = string
}

variable "config_s3_key" {
  description = "S3 key for config file"
  type        = string
}

variable "lambda_tags" {
  description = "Tags specific to Lambda function"
  type        = map(string)
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "log_encryption_key" {
  description = "KMS key ARN for CloudWatch Logs encryption"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
