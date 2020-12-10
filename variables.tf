data "aws_caller_identity" "current" {
}

variable "appsync_graphql_api_id" {
  type = string
}

variable "app" {
  type        = string
  description = "Mnemonic label for the service you are performing key rotation for, i.e. 'sor'"
}

locals {
  account_id = data.aws_caller_identity.current.account_id

  key_rotation_secrets_name = "key_rotation_secrets_${var.app}_${local.environment_name}"

  key_rotation_secrets_arn = "arn:aws:secretsmanager:eu-west-2:${local.account_id}:secret:${local.key_rotation_secrets_name}*"

  environment_name = terraform.workspace

  region = "eu-west-2"

}
