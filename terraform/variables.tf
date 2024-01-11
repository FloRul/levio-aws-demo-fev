variable "aws_region" {
  default = "us-west-2"
}
variable "db_admin_user" {
  default = "postgres_admin"
}
variable "db_name" {
  default = "vector_db"
}
variable "jumpbox_instance_type" {
  default = "t2.micro"
}

variable "ingestion_lambda_image_uri" {
  type     = string
  nullable = false
}
