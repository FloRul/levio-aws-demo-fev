variable "lambda_function_name" {
  nullable = false
}

variable "lambda_image_uri" {
  nullable = false
}

variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "lambda_vpc_security_group_ids" {
  type     = list(string)
  nullable = false
}

variable "lambda_vpc_subnet_ids" {
  type     = list(string)
  nullable = false
}
variable "pg_vector_host" {
  type     = string
  nullable = false
}

variable "pg_vector_port" {
  type     = number
  nullable = false
}

variable "pg_vector_database" {
  type     = string
  nullable = false
}

variable "pg_vector_user" {
  type     = string
  nullable = false
}

variable "pg_vector_driver" {
  type     = string
  nullable = false
  default  = "psycopg2"
}

variable "pg_vector_password_secret_name" {
  type     = string
  nullable = false
}

variable "secret_arn" {
  type     = string
  nullable = false
}

variable "memory_lambda_name" {
  type     = string
  nullable = false
}

variable "dynamo_history_table_name" {
  type     = string
  nullable = false
}
