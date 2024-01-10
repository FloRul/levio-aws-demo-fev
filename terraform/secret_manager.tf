
data "aws_secretsmanager_secret" "password" {
  depends_on = [aws_secretsmanager_secret.password]
  name       = aws_secretsmanager_secret.password.name
}

data "aws_secretsmanager_secret_version" "password" {
  depends_on = [aws_secretsmanager_secret.password]
  secret_id  = data.aws_secretsmanager_secret.password.id
}

resource "random_password" "master" {
  length           = 16
  special          = true
  override_special = "_!%^"
}

resource "random_pet" "secret_name" {
  length    = 3
  separator = "-"
}

resource "aws_secretsmanager_secret" "password" {
  name = "vectordb-password-main-${random_pet.secret_name.id}"
}

resource "aws_secretsmanager_secret_version" "password" {
  secret_id     = aws_secretsmanager_secret.password.id
  secret_string = random_password.master.result
}
