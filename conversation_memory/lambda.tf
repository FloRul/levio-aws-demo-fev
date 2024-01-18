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
    DYNAMO_TABLE = var.dynamo_history_table_name
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
  }
}
