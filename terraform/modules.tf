module "ingestion" {
  source              = "../ingestion"
  storage_bucket_name = "levio-demo-fev-storage"
  vpc_id              = module.vpc.vpc_id
  lambda_vpc_security_group_ids = [
    module.vpc.default_security_group_id,
  ]
  pg_vector_host             = aws_db_instance.vector_db.address
  pg_vector_port             = aws_db_instance.vector_db.port
  pg_vector_database         = aws_db_instance.vector_db.name
  pg_vector_user             = aws_db_instance.vector_db.username
  ingestion_lambda_image_uri = "levio-demo-fev-ingestion:latest"
}
