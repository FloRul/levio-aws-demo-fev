module "ingestion" {
  source              = "../ingestion"
  storage_bucket_name = "levio-demo-fev-storage"
  lambda_vpc_security_group_ids = [
    aws_security_group.lambda_ingestion_sg.id,
  ]
  lambda_vpc_subnet_ids          = module.vpc.public_subnets
  pg_vector_host                 = aws_db_instance.vector_db.address
  pg_vector_port                 = aws_db_instance.vector_db.port
  pg_vector_database             = aws_db_instance.vector_db.db_name
  pg_vector_user                 = aws_db_instance.vector_db.username
  pg_vector_password_secret_name = aws_secretsmanager_secret.password.name
  secret_arn                     = aws_secretsmanager_secret.password.arn
  ingestion_lambda_image_uri     = var.ingestion_lambda_image_uri
  lambda_function_name           = "levio-demo-fev-ingestion"
  queue_name                     = "levio-demo-fev-ingestion-queue"
}
