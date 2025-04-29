resource "aws_dynamodb_table" "incidents" {
  name           = var.table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "IncidentId"
  
  attribute {
    name = "IncidentId"
    type = "S"
  }

  tags = var.tags
}

output "table_name" {
  value = aws_dynamodb_table.incidents.name
}

output "table_arn" {
  value = aws_dynamodb_table.incidents.arn
}
