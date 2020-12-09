resource "null_resource" "build" {

  provisioner "local-exec" {
    command     = "lambda-build.sh"
    interpreter = ["sh"]
    working_dir = path.module
  }

  triggers = {
    "before" = aws_iam_role.sor_appsync_key_rotation_lambda.id
  }
}