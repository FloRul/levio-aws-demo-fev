module "lambda_function_container_image" {
  source                 = "terraform-aws-modules/lambda/aws"
  function_name          = var.lambda_function_name
  create_package         = false
  image_uri              = var.ingestion_lambda_image_uri
  package_type           = "Image"
  vpc_subnet_ids         = var.lambda_vpc_subnet_ids
  vpc_security_group_ids = var.lambda_vpc_security_group_ids
  environment_variables = {
    PGVECTOR_DRIVER               = "psycopg2"
    PGVECTOR_HOST                 = var.pg_vector_host
    PGVECTOR_PORT                 = var.pg_vector_port
    PGVECTOR_DATABASE             = var.pg_vector_database
    PGVECTOR_USER                 = var.pg_vector_user
    PGVECTOR_COLLECTION_NAME      = "emails-embeddings"
    PGVECTOR_PASSWORD_SECRET_NAME = var.pg_vector_password_secret_name
  }
}

# resource "aws_lambda_permission" "this" {
#   depends_on    = [module.lambda_function_container_image]
#   statement_id  = "AllowExecutionFromAPIGateway"
#   action        = "lambda:InvokeFunction"
#   function_name = var.lambda_function_name
#   principal     = "apigateway.amazonaws.com"
#   source_arn    = "${var.api_execution_arn}/*/*/*"
# }
