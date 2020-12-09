resource "null_resource" "build" {

  provisioner "local-exec" {
    command     = "lambda-build.sh"
    interpreter = ["sh"]
    working_dir = path.module
  }

  hash = filebase64sha256("./lambda/key-rotator-appsync.zip")
}