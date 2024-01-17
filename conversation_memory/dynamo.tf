data "aws_dynamodb_table" "person_table" {
  name = "Person"
}

resource "aws_dynamodb_table" "basic-conversation_memory_table-table" {
  name         = var.dynamo_history_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "PK"
  range_key    = "SK"

  attribute {
    // Timestamp
    name = "SK"
    type = "S"
  }

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "CaseId"
    type = "S"
  }

  attribute {
    name = "HumanMessage"
    type = "S"
  }

  attribute {
    name = "AssistantMessage"
    type = "S"
  }
  global_secondary_index {
    name            = "CaseId-SK-index"
    hash_key        = "CaseId"
    range_key       = "SK"
    projection_type = "ALL"
  }
}
