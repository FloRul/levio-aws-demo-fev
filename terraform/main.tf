terraform {
  backend "s3" {
    bucket = "levio-aws-demo-fev-terraform"
    key    = "state/terraform.tfstate"
    region = "us-west-2"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
  default_tags {
    tags = {
      Environment = "dev"
      Terraform   = "true"
      Project     = "levio-aws-demo-fev"
    }
  }
}


