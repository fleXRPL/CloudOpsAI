locals {
  name_prefix = "cloudopsai-${var.environment}"
}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["CloudOpsAI", "Errors", "FunctionName", var.function_name],
            ["CloudOpsAI", "Duration", "FunctionName", var.function_name],
            ["CloudOpsAI", "Invocations", "FunctionName", var.function_name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Metrics"
        }
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Lambda function error rate"
  alarm_actions       = var.alarm_actions

  dimensions = {
    FunctionName = var.function_name
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = var.log_group_name
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_cloudwatch_log_metric_filter" "ai_decision_duration" {
  name           = "${local.name_prefix}-ai-decision-time"
  pattern        = "[timestamp, requestId, duration]"
  log_group_name = var.log_group_name

  metric_transformation {
    name          = "AIDecisionDuration"
    namespace     = "CloudOpsAI"
    value         = "$duration"
    default_value = 0
  }
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}
