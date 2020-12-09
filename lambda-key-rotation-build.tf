resource "null_resource" "build" {

  provisioner "local-exec" {
      command = "lambda-build.sh"
      interpreter = ["sh"]
      working_dir = "${path.module}"
  }
}