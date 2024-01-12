output "vpc_id" {
  value = module.vpc.vpc_id
}

output "instance_ip" {
  value = aws_instance.jumpbox.public_ip
}

output "rds_instance_dns" {
  value = aws_db_instance.vector_db.address
}
