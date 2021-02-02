# key-rotator-appsync

## Overview

This provides a terraform module that deploys a lambda to carry out key rotation on an AWS AppSync API, and the CloudWatch event trigger to schedule it.

It feeds a partner process app in IBM's *Business Automation Workflow* (BAW) that performs the actual updating of the environment variables within one or more process apps that need to access the AppSync API. Specifically, environment variables are:

* `GRAPHQL_API_KEY` - the new key that was just generated
* `GRAPHQL_SERVER` - the full URL to the AppSync API. This includes the base path of `/graphql`

## Usage & Configuration

### Terraform

For the service you want to perform key rotation on, you will need to pull this module into the main, AppSync-deploying terraform by including, e.g.

```hcl
module "key_rotator" {
  source                 = "github.com/ONSdigital/key-rotator-appsync"
  appsync_graphql_api_id = aws_appsync_graphql_api.sor.id
  app                    = "sor"
}
```

* `appsync_graphql_api_id` - the API id for the AppSync service you wish to rotate keys on.
* `app` - a short mnemonic label that (i.e. with git branch), forms a unique name for the AWS Secrets Manager secret within the deployment account/environment, with the template `key_rotation_secrets_${var.app}`

You should review the value of the terraform local variable `cron_string` to ensure it will be triggered as you expect, and `ttl_seconds` if you want something other than a one week key lifetime.

### Secrets

The more sensitive configuration items are drawn from the AWS Secrets Manager secret mentioned above. It consists of the following fields:

* `BPM_USER` and `BPM_PW` - the username and password for the BAW service user that has permissions to start the environment variable updater process app.
* `BASE_URL` - the first part of the URL for the REST requests. It has the form `https://HOSTNAME/dba/ENVIRONMENT` with no trailing slash.

### Post-deployment

After deployment, you will need to edit the lambda's `BAW_CONTAINERS` environment variable to be a JSON list of strings of the BAW containers that you wish to update, e.g. `["EXAMPLE", "FINANCE"]`. This must be a subset of the PermittedContainers EPV associated with the BAW process app, or the request will be rejected.
