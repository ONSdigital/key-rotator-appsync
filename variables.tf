data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

variable "appsync_graphql_api_id" {
  type = string
}

variable "app" {
  type        = string
  description = "Unique, mnemonic label for the service you are performing key rotation for, i.e. 'sor_dev_master'"
}

variable "cron_schedule" {
  type        = string
  description = "Cron schedule expression e.g. 'cron(7 0 * * ? *)'"
  default     = "cron(7 0 * * ? *)"
}

locals {
  account_id = data.aws_caller_identity.current.account_id

  ttl_seconds = "604800" // 86400 is one day in seconds, 604800 is a week

  key_rotation_secrets_name = "key_rotation_secrets_${var.app}"

  key_rotation_secrets_arn = "arn:aws:secretsmanager:${data.aws_region.current.name}:${local.account_id}:secret:${local.key_rotation_secrets_name}*"

}

output "secret_name" {
  value = local.key_rotation_secrets_name
}
