resource "null_resource" "build" {
  // timestamp() forces this resource to be built
  // every time (otherwise tf does this once and
  // never again, so lambda zip isn't present)
  triggers = {
    always_run = timestamp()
  }
  provisioner "local-exec" {
    command     = "lambda-build.sh"
    interpreter = ["sh"]
    working_dir = path.module
  }
}