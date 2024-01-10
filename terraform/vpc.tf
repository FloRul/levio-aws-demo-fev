data "aws_availability_zones" "available" {}

locals {
  name     = "ex-${basename(path.cwd)}"
  vpc_cidr = "10.0.0.0/16"
  azs      = slice(data.aws_availability_zones.available.names, 0, 2)
}

module "vpc" {
  source                             = "terraform-aws-modules/vpc/aws"
  name                               = local.name
  cidr                               = local.vpc_cidr
  azs                                = local.azs
  public_subnets                     = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k)]
  database_subnets                   = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 4)]
  create_database_subnet_route_table = true
  create_database_subnet_group       = true
  create_igw                         = true
}

resource "aws_vpc_endpoint" "secrets_manager_endpoint" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  security_group_ids  = [aws_security_group.sm_sg.id]
  subnet_ids          = module.vpc.public_subnets
  private_dns_enabled = true
}

resource "aws_vpc_endpoint" "bedrock_endpoint" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  security_group_ids  = [aws_security_group.sm_sg.id]
  subnet_ids          = module.vpc.public_subnets
  private_dns_enabled = true
}

resource "aws_security_group" "bedrock_sg" {
  name   = "bedrock-runtime-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    description = "Bedrock runtime sg"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Bedrock runtime sg"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "sm_sg" {
  name   = "secret-manager-sg"
  vpc_id = module.vpc.vpc_id
  ingress {
    description = "Secrets Manager"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Secrets Manager"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
