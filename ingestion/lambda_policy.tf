data "aws_iam_policy_document" "lambda_policy_doc" {
  statement {
    sid    = "AllowCreatingLogGroups"
    effect = "Allow"

    resources = [
      "arn:aws:logs:*:*:*"
    ]

    actions = [
      "logs:CreateLogGroup"
    ]
  }

  statement {
    sid    = "AllowWritingLogs"
    effect = "Allow"

    resources = [
      "arn:aws:logs:*:*:log-group:/aws/${var.lambda_function_name}/*:*"
    ]

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
  statement {
    sid    = "AllowBedrockUsage"
    effect = "Allow"

    resources = [
      "*"
    ]

    actions = [
      "bedrock:*"
    ]
  }
  statement {
    sid    = "AllowRDSConnectReadWrite"
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
  statement {
    sid    = "AllowAccessNetworkInterface"
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
  statement {
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      var.pg_vector_password_secret_name
    ]
  }
}
