resource "aws_iam_role" "lambda_role" {
  name               = "${var.lambda_function_name}-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      }
    }
  ]
}
EOF
}

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

resource "aws_iam_policy" "lambda_iam_policy" {
  name   = "${var.lambda_function_name}-policy"
  policy = data.aws_iam_policy_document.lambda_policy_doc.json
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_iam_policy.arn
  role       = aws_iam_role.lambda_role.name
}
