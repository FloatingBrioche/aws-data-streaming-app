# aws-data-streaming-app
[![tests-and-deployment](https://github.com/FloatingBrioche/aws-data-streaming-app/actions/workflows/test_and_deploy.yaml/badge.svg)](https://github.com/FloatingBrioche/aws-data-streaming-app/actions/workflows/test_and_deploy.yaml) 
[![Coverage](https://github.com/FloatingBrioche/aws-data-streaming-app/blob/main/docs/coverage.svg)](https://github.com/FloatingBrioche/aws-data-streaming-app/blob/main/docs/coverage.txt) 
[![PEP8](https://img.shields.io/badge/PEP8-compliant-limegreen.svg)](https://www.python.org/dev/peps/pep-0008/) 
[![bandit security check](https://img.shields.io/badge/security_issues-0-limegreen.svg)](https://github.com/FloatingBrioche/aws-data-streaming-app/blob/main/docs/security_check.txt)

This application has been designed to allow the Northcoders marketing team to search for and ingest articles from the Guardian API. The application uses the Python requests library to submit a get request to the API's "search" endpoint using the passed query. Any resulting articles are then uploaded to an AWS SQS queue to be analysed for relevance and suitability downstream.

The app uses employs a "fail-fast" approach using Pydantic validation to prevent unnecessary API requests and Lambda execution time for invalid queries. Thorough logging, monitoring and alarms are provdided via CloudWatch to ensure proper functioning of the application and adherence to rate limits. CI/CD is provided via a GitHub Actions pipeline and Terraform IaC.

The application could be expanded to make requests to and aggregate responses from multiple APIs.

## Technologies

- Python 3.12.3
    - requests
    - boto3
    - pydantic
    - bandit
    - pytest
    - coverage
- AWS
    - Lambda
    - SQS
    - Secrets Manager
    - CloudWatch
    - S3
    - SNS
- DevOps
    - GitHub Actions
    - Terraform
- APIs
    - [Guardian API](https://open-platform.theguardian.com/documentation/)

## Prerequisites

- An AWS IAM user with CLI access keys
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [Terraform ~> v5.85.0](https://developer.hashicorp.com/terraform/install)
- A [Guardian API access key](https://open-platform.theguardian.com/access/)
- Python 3.12.3

## Setup Instructions

1. **Fork the repo**

2. **Clone the repo**  
   ```bash  
   git clone https://github.com/FloatingBrioche/aws-data-streaming-app.git
   cd aws-data-streaming-app 
   ``` 

3. **Add your Guardian API key to your AWS Secrets Manager**
    ```bash
    aws secretsmanager create-secret \
    --name Guardian-API-Key \
    --description "Access key for Guardian API." \
    --secret-string "[ADD YOUR API KEY HERE]"
    ```

4. **Retrieve and note your secret ARN**
- Retrive the ARN using the below CLI command. Note it to use in two of the following step.
    ```bash 
    aws secretsmanager describe-secret \
    --secret-id Guardian-API-Key --query 'ARN' --output text
    ```

4. **Create your .tfvars file**
    ```bash
    cat > terraform/terraform.tfvars << EOF
    project_owner_email = "[ADD PROJECT OWNER EMAIL]"
    secret_arn = "[ADD SECRET ARN]"
    EOF
    ```

5. **Create your Terraform State Bucket**
    ```bash
    aws s3api create-bucket \
    --bucket [ADD YOUR BUCKET NAME] \
    --region [ADD YOUR REGION] \
    --create-bucket-configuration LocationConstraint=[YOUR REGION]
    ```

6. **Update the Terraform fields**
    - Update the backend bucket in the [Terraform providers file](terraform/providers.tf)
    - Update the vars in the [Terraform directory](./terraform/vars.tf)        

7. **Add repo secrets to enable CI pipeline**

- Go to Settings > Secrets and variables > Actions.
- Click New repository secret.
- Add the following secrets:
    - AWS_ACCESS_KEY
    - AWS_SECRET_ACCESS_KEY
    - PROJECT_OWNER_EMAIL
    - SECRET_ARN

8. **Run Terraform init, plan and apply**

- `cd terraform`
- `terraform init`
- `terraform plan`
- `terraform apply`

## **Teardown instructions**

- In the terraform directory, run `terraform destroy`

## **Tests and checks**

A Makefile is provided using which 

## Usage

The app can be used via AWS CLI. The payload has two required keys – "SearchTerm" and "queue" – and two optional keys – "FromDate" and "ToDate". The values must conform to the [LambdaEvent model](https://github.com/FloatingBrioche/aws-data-streaming-app/blob/main/lambda_app/lambda_classes.py).

Example payload:

                {
                "SearchTerm": "scary futuristic blobs",
                "FromDate": "2015-12-17",
                "ToDate": "2024-01-01",
                "queue": "guardian_content"
                }

AWS CLI command:

```bash
aws lambda invoke \
    --cli-binary-format raw-in-base64-out \
    --function-name data_streaming_lambda \
    --cli-binary-format raw-in-base64-out \
    --payload '{
                "SearchTerm": "[ADD SEARCH TERM]",
                "FromDate": "[ADD DATE]",
                "ToDate": "[ADD DATE]",
                "queue": "guardian_content"
                }' \
    lambda-response.json
```