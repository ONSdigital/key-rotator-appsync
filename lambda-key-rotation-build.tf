resource "null_resource" "build" {
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = "lambda-build.sh"
    interpreter = ["sh"]
    working_dir = path.module
  }
}