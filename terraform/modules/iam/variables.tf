variable "function_name" {
  description = "Name prefix for IAM roles and policies"
  type        = string
}

variable "config_s3_bucket" {
  description = "S3 bucket ARN for config files"
  type        = string
}

variable "kms_key_arn" {
  description = "KMS key ARN for encryption"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
