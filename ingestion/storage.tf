resource "aws_s3_bucket" "ingestion_source_storage" {
  bucket = var.storage_bucket_name
}

