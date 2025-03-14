variable "project_owner" {
  description = "Name to be used for project owner in resource tags"
  type        = string
  default     = "Martin C."
}

variable "project_owner_email" {
  description = "Email to be used for SNS notifications of critical errors"
  type        = string
}

variable "project_name" {
  type    = string
  default = "data-streaming-app"
}

variable "department" {
  description = "Department name to be used in resource tags"
  type        = string
  default     = "Data Engineering"
}

variable "retention_date" {
  description = "Retention date to be used in resource tags"
  type        = string
  default     = "2025-03-31"
}

variable "secret_arn" {
  description = "ARN of the secret containing the API key"
  type        = string
  sensitive   = true
}

variable "lambda_name" {
  description = "Name to be given to lambda function"
  type        = string
  default     = "data_streaming_lambda"
}