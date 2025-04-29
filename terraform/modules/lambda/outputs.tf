output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.noc_agent.arn
}

output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.noc_agent.function_name
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Log Group"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}
