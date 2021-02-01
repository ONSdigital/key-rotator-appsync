data "aws_caller_identity" "current" {
}

variable "appsync_graphql_api_id" {
  type = string
}

variable "app" {
  type        = string
  description = "Mnemonic label for the service you are performing key rotation for, i.e. 'sor'"
}

variable "cron_schedule" {
  type        = string
  description = "Cron schedule expression e.g. 'cron(7 0 * * ? *)'"
  default     = "cron(7 0 * * ? *)"
}

locals {
  account_id = data.aws_caller_identity.current.account_id

  ttl_seconds = "604800" // 86400 is one day in seconds, 604800 is a week

  key_rotation_secrets_name = "key_rotation_secrets_${var.app}_${local.environment_name}"

  key_rotation_secrets_arn = "arn:aws:secretsmanager:eu-west-2:${local.account_id}:secret:${local.key_rotation_secrets_name}*"

  environment_name = terraform.workspace

  region = "eu-west-2"

}

output "secret_name" {
  value = local.key_rotation_secrets_name
}
