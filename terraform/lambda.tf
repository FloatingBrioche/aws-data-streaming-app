data "archive_file" "lambda" {
    type        = "zip"
    source_dir  = "${path.module}/../lambda_app"
    output_path = "${path.module}/../zip_files/lambda_app.zip"

}


resource "aws_lambda_function" "data_streaming_lambda" {
  function_name    = var.lambda_name
  source_code_hash = data.archive_file.lambda.output_base64sha256
  s3_bucket        = aws_s3_bucket.code_bucket.bucket
  s3_key           = aws_s3_object.lambda_code.key
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  timeout          = 180
  layers           = [aws_lambda_layer_version.dependencies.arn]

  depends_on = [aws_s3_object.lambda_code, aws_s3_object.layer_code]


}

### IAM ###

## IAM Role 

resource "aws_iam_role" "lambda_role" {
  name        = "data-streaming-lambda-role"
  assume_role_policy = <<EOF
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sts:AssumeRole"
                ],
                "Principal": {
                    "Service": [
                        "lambda.amazonaws.com"
                    ]
                }
            }
        ]
    }
    EOF
}

## IAM Policies ##

# CloudWatch

data "aws_iam_policy_document" "cw_document" {
  statement {
    actions = ["logs:CreateLogGroup"]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
    ]
  }

  statement {
    actions = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = [
      "${aws_cloudwatch_log_group.lambda_log_group.arn}:*"
    ]
  }
}

resource "aws_iam_policy" "cw_policy" {
  name = "data-lambda-cw-policy"
  policy      = data.aws_iam_policy_document.cw_document.json
}

resource "aws_iam_role_policy_attachment" "lambda_cw_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.cw_policy.arn
}

# SecretsManager

data "aws_iam_policy_document" "secrets_manager_document" {
  statement {
        actions = ["secretsmanager:GetSecretValue"] 
        resources = [var.secret_arn]
    }
}

resource "aws_iam_policy" "secrets_manager_policy" {
  name = "data-lambda-secrets_manager-policy"
  policy      = data.aws_iam_policy_document.secrets_manager_document.json
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.secrets_manager_policy.arn
}

# SQS

data "aws_iam_policy_document" "sqs_document" {
  statement {
        actions = ["sqs:GetQueueUrl", "sqs:SendMessage"] 
        resources = [aws_sqs_queue.guardian_content_queue.arn]
    }
}

resource "aws_iam_policy" "sqs_policy" {
  name = "data-lambda-sqs-policy"
  policy      = data.aws_iam_policy_document.sqs_document.json
}

resource "aws_iam_role_policy_attachment" "lambda_sqs_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.sqs_policy.arn
}


### Test invocation

resource "aws_lambda_invocation" "test" {
  function_name = aws_lambda_function.data_streaming_lambda.function_name
  input = jsonencode({
    SearchTerm = "recursion immersion"
  })

  depends_on = [ aws_sqs_queue.guardian_content_queue ]
}

output "result_entry" {
  value = jsondecode(aws_lambda_invocation.test.result)
}