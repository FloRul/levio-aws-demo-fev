module "lambda_function_container_image" {
  timeout                  = 500
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
    sqs = {
      effect = "Allow"

      resources = [
        aws_sqs_queue.queue.arn
      ]

      actions = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ]
    }
    s3 = {
      effect = "Allow"

      resources = [
        aws_s3_bucket.ingestion_source_storage.arn,
        "${aws_s3_bucket.ingestion_source_storage.arn}/*"
      ]

      actions = [
        "s3:*"
      ]
    }
  }
}
