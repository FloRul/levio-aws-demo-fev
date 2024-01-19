module "lambda_function_container_image" {
  timeout                  = 60
  source                   = "terraform-aws-modules/lambda/aws"
  function_name            = var.lambda_function_name
  create_package           = false
  image_uri                = var.lambda_image_uri
  package_type             = "Image"
  memory_size              = 1024
  vpc_subnet_ids           = var.lambda_vpc_subnet_ids
  vpc_security_group_ids   = var.lambda_vpc_security_group_ids
  role_name                = "${var.lambda_function_name}-role"
  attach_policy_statements = true

  environment_variables = {
    PGVECTOR_DRIVER               = "psycopg2"
    PGVECTOR_HOST                 = var.pg_vector_host
    PGVECTOR_PORT                 = var.pg_vector_port
    PGVECTOR_DATABASE             = var.pg_vector_database
    PGVECTOR_USER                 = var.pg_vector_user
    PGVECTOR_PASSWORD_SECRET_NAME = var.pg_vector_password_secret_name
    MAX_TOKENS                    = 600
    ENABLE_INFERENCE              = 1
    ENABLE_HISTORY                = 1
    ENABLE_RETRIEVAL              = 1
    MEMORY_LAMBDA_NAME            = var.memory_lambda_name
    DYNAMO_TABLE                  = var.dynamo_history_table_name
    TOP_K                         = 50
    TEMPERATURE                   = 0.5
    TOP_P                         = 0.9
    RELEVANCE_THRESHOLD           = 0.65
    MODEL_ID                      = "anthropic.claude-v2"
    EMBEDDING_COLLECTION_NAME     = var.embedding_collection_name
    SYSTEM_PROMPT                 = "Answer in four to five sentences.Answer in french, do not use XML tags in your answer."
    CHAT_INTENT_NAME              = "global"
  }
  policy_statements = {
    log_group = {
      effect = "Allow"
      actions = [
        "logs:CreateLogGroup"
      ]
      resources = [
        "arn:aws:logs:*:*:*"
      ]
    }
    log_write = {
      effect = "Allow"

      resources = [
        "arn:aws:logs:*:*:log-group:/aws/${var.lambda_function_name}/*:*"
      ]

      actions = [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
      ]
    }
    bedrock_usage = {
      effect = "Allow"

      resources = [
        "*"
      ]

      actions = [
        "bedrock:*"
      ]
    }
    rds_connect_readwrite = {
      effect = "Allow"

      resources = [
        "arn:aws:rds:${var.aws_region}:446872271111:db:${var.pg_vector_database}"
      ]

      actions = [
        "rds-db:connect",
        "rds-db:execute-statement",
        "rds-db:rollback-transaction",
        "rds-db:commit-transaction",
        "rds-db:beginTransaction"
      ]
    }
    access_network_interface = {
      effect = "Allow"

      resources = [
        "*"
      ]

      actions = [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface"
      ]
    }
    secretsmanager = {
      effect = "Allow"

      resources = [
        var.secret_arn
      ]

      actions = [
        "secretsmanager:GetSecretValue"
      ]
    }
    dynamo_db = {
      effect = "Allow"

      resources = [
        "arn:aws:dynamodb:${var.aws_region}:446872271111:table/${var.dynamo_history_table_name}"
      ]

      actions = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query",
        "dynamodb:BatchWriteItem",
        "dynamodb:BatchGetItem"
      ]
    }
    lambda = {
      effect = "Allow"

      resources = [
        "arn:aws:lambda:${var.aws_region}:446872271111:function:${var.memory_lambda_name}"
      ]

      actions = [
        "lambda:InvokeFunction"
      ]
    }
  }
}
