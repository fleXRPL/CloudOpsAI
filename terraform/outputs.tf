output "lambda_function_arn" {
  description = "ARN of the CloudOpsAI Lambda function"
  value       = module.lambda.function_arn
}

output "log_group_name" {
  description = "Name of the CloudWatch Log Group"
  value       = module.lambda.cloudwatch_log_group_name
}

output "config_bucket" {
  description = "S3 bucket containing CloudOpsAI configuration"
  value       = module.s3.bucket_name
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.function_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "config_bucket_name" {
  description = "Name of the configuration S3 bucket"
  value       = module.s3.bucket_name
}
