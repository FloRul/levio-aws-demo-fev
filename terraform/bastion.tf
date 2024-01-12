data "aws_ami" "latest_amazon_linux" {
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["amazon"]
}

resource "aws_instance" "jumpbox" {
  ami                         = data.aws_ami.latest_amazon_linux.id
  instance_type               = var.jumpbox_instance_type
  key_name                    = "bastion-rds"
  subnet_id                   = module.vpc.public_subnets[0]
  vpc_security_group_ids      = [aws_security_group.jumpbox_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "jumpbox-instance"
  }
}


