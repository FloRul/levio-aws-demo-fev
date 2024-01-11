module "ingestion" {
  source              = "../ingestion"
  storage_bucket_name = "levio-demo-fev-storage"
  lambda_vpc_security_group_ids = [
    module.vpc.default_security_group_id,
  ]
  lambda_vpc_subnet_ids          = module.vpc.public_subnets
  pg_vector_host                 = aws_db_instance.vector_db.address
  pg_vector_port                 = aws_db_instance.vector_db.port
  pg_vector_database             = aws_db_instance.vector_db.db_name
  pg_vector_user                 = aws_db_instance.vector_db.username
  pg_vector_password_secret_name = aws_secretsmanager_secret_version.password.secret_id
  ingestion_lambda_image_uri     = "levio-demo-fev-ingestion:latest"
  lambda_function_name           = "levio-demo-fev-ingestion"
}
