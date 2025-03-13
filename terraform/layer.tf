resource "null_resource" "create_dependencies" {
  provisioner "local-exec" {
    command = "pip install -r ${path.module}/../layer_requirements.txt --python-version 3.12 --platform manylinux2014_x86_64 -t ${path.module}/../layer/python --only-binary=:all: pydantic"
  }

  # triggers = {
  #   dependencies = filemd5("${path.module}/../layer_requirements.txt")
  # }
}


data "archive_file" "layer" {
    type = "zip"
    source_dir =  "${path.module}/../layer" 
    output_path =  "${path.module}/../zip_files/layer.zip"

    depends_on = [ null_resource.create_dependencies ]

}


resource "aws_lambda_layer_version" "dependencies" {
  layer_name = "requests_pydantic_layer"
  s3_bucket  = aws_s3_object.layer_code.bucket
  s3_key     = aws_s3_object.layer_code.key
}