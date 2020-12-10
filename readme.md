# key-rotator-appsync

## Overview

This provides a terraform module that deploys a lambda to carry out key rotation on an AWS AppSync API, and the CloudWatch event trigger to schedule it.

## Usage & Configuration

For the service you want to perform key rotation on, you will need to pull this module into the main, AppSync-deploying terraform by including, e.g.

```hcl
module "key-rotator" {
  source                 = "github.com/ONSdigital/key-rotator-appsync"
  appsync_graphql_api_id = aws_appsync_graphql_api.sor.id
  app                    = "sor"
}
```

* `appsync_graphql_api_id` should be the API id for the AppSync service you wish to rotate keys on.
* `app` should be a short mnemonic label that, along with the terraform workspace (i.e. git branch), forms a unique name for the AWS Secrets Manager secret, with the template `key_rotation_secrets_${var.app}_${local.environment_name}`

You should review the value of the terraform local variable `cron_string` to ensure it will be triggered as you expect.
