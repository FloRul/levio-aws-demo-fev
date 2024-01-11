# data "aws_ami" "latest_amazon_linux" {
#   most_recent = true

#   filter {
#     name   = "name"
#     values = ["amzn2-ami-hvm-*-x86_64-gp2"]
#   }

#   filter {
#     name   = "virtualization-type"
#     values = ["hvm"]
#   }

#   owners = ["amazon"]
# }

# resource "tls_private_key" "jumpbox" {
#   algorithm = "RSA"
#   rsa_bits  = 4096
# }

# resource "aws_key_pair" "jumpbox" {
#   key_name   = "jumpbox-key-pair"
#   public_key = tls_private_key.jumpbox.public_key_openssh
# }

# resource "aws_instance" "jumpbox" {
#   ami                         = data.aws_ami.latest_amazon_linux.id
#   instance_type               = var.jumpbox_instance_type
#   key_name                    = aws_key_pair.jumpbox.key_name
#   subnet_id                   = module.vpc.public_subnets[0]
#   vpc_security_group_ids      = [aws_security_group.jumpbox_sg.id]
#   associate_public_ip_address = true

#   tags = {
#     Name = "jumpbox-instance"
#   }
# }

# resource "aws_security_group" "jumpbox_sg" {
#   name   = "jumpbox-sg"
#   vpc_id = module.vpc.vpc_id

#   ingress {
#     from_port   = 22
#     to_port     = 22
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }
