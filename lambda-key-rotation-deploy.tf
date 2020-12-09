//---------------------------------------------------------
// Role Setup

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "sor_appsync_key_rotation_lambda" {
  name               = "spp-bw-sor-key_rotation-${local.environment_name}"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

/*
  The basic policy covers logging permissions
*/
resource "aws_iam_role_policy_attachment" "sor_appsync_key_rotation_lambda_logging" {
  role       = aws_iam_role.sor_appsync_key_rotation_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "key_rotation_baw_secret" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      local.key_rotation_secrets_arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "appsync:CreateApiKey",
      "appsync:GetGraphqlApi"
    ]
    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role_policy" "sor_appsync_key_rotation_lambda" {
  role   = aws_iam_role.sor_appsync_key_rotation_lambda.id
  policy = data.aws_iam_policy_document.key_rotation_baw_secret.json
}

//---------------------------------------------------------
// The Lambda function

resource "aws_lambda_function" "sor_appsync_key_rotation" {
  depends_on = [null_resource.build]

  function_name = "sor-appsync-key_rotation-${local.environment_name}"

  filename         = "./lambda/key-rotator-appsync.zip"
  //source_code_hash = filebase64sha256("./lambda/key-rotator-appsync.zip")

  runtime = "python3.8"

  role = aws_iam_role.sor_appsync_key_rotation_lambda.arn

  handler = "lambda_function.lambda_handler"

  timeout = 60

  environment {
    variables = {
      TTL_SECONDS    = "604800" // 86400 is one day in seconds 604800 is a week
      SECRET         = local.key_rotation_secrets_name
      API_ID         = var.appsync_graphql_api_id
      BAW_CONTAINERS = "[]" // JSON formatted list
    }
  }
}

//---------------------------------------------------------
// CloudWatch Event (the scheduler)

resource "aws_cloudwatch_event_rule" "appsync_key_rotation_daily" {
  name                = "every-24-hours"
  description         = "Fires every 24 hours"
  schedule_expression = "cron(38 17 * * ? *)"
}

resource "aws_cloudwatch_event_target" "appsync_key_rotation" {
  rule = aws_cloudwatch_event_rule.appsync_key_rotation_daily.name
  arn  = aws_lambda_function.sor_appsync_key_rotation.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_key_rotation" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sor_appsync_key_rotation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.appsync_key_rotation_daily.arn
}
