data "aws_dynamodb_table" "person_table" {
  name = "Person"
}

resource "aws_dynamodb_table" "basic-conversation_memory_table-table" {
  name         = var.dynamo_history_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "SessionId"
  range_key    = "SK"

  attribute {
    // Timestamp
    name = "SK"
    type = "S"
  }

  attribute {
    name = "SessionId"
    type = "S"
  }
}
