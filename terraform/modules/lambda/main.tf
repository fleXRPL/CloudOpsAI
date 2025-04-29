locals {
  name_prefix = "cloudopsai-${var.environment}"
}

resource "aws_lambda_layer_version" "ai_noc_dependencies" {
  filename            = "../dist/lambda-layer.zip"
  layer_name          = "${local.name_prefix}-dependencies"
  compatible_runtimes = ["python3.12"]
  description         = "Dependencies for AI NOC Agent"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/function.zip"
}

resource "aws_lambda_function" "noc_agent" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name    = var.function_name
  role            = var.lambda_role_arn
  handler         = "index.handler"
  runtime         = var.runtime
  timeout         = 300
  memory_size     = 256

  vpc_config {
    subnet_ids         = var.vpc_config.subnet_ids
    security_group_ids = var.vpc_config.security_group_ids
  }

  environment {
    variables = {
      CONFIG_BUCKET = var.config_s3_bucket
      CONFIG_KEY    = var.config_s3_key
      ENVIRONMENT   = var.environment
    }
  }

  tags = var.lambda_tags
}

output "function_name" {
  value = aws_lambda_function.noc_agent.function_name
}

output "function_arn" {
  value = aws_lambda_function.noc_agent.arn
}

resource "aws_cloudwatch_event_rule" "cloudwatch_alarms" {
  name        = "capture-cloudwatch-alarms"
  description = "Capture CloudWatch Alarm state changes"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.cloudwatch_alarms.name
  target_id = "SendToLambda"
  arn       = aws_lambda_function.noc_agent.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.noc_agent.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cloudwatch_alarms.arn
}

# Add CloudWatch Logs retention
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14

  tags = var.lambda_tags
}
