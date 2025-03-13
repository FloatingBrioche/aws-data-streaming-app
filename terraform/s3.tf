resource "aws_s3_bucket" "code_bucket" {
  bucket_prefix = "${var.project_name}-code-bucket"
}


resource "aws_s3_object" "lambda_code" {
  bucket      = aws_s3_bucket.code_bucket.id
  key         = "lambda_code_package"
  source      = "${path.module}/../zip_files/lambda_app.zip"
  source_hash = data.archive_file.lambda.output_base64sha256
}


resource "aws_s3_object" "layer_code" {
  bucket      = aws_s3_bucket.code_bucket.id
  key         = "lambda_layer_package"
  source      = "${path.module}/../zip_files/layer.zip"
  source_hash = data.archive_file.layer.output_base64sha256
}