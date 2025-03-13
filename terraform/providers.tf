terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.85.0"
    }
  }

  backend "s3" {
    bucket = "mc-guardian-data-streaming-terraform-state-bucket"
    key    = "terraform-perm.tfstate"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
  default_tags {
    tags = {
      ProjectName   = "Guardian Data Streaming App"
      Owner         = var.project_owner
      Department    = var.department
      DeployedFrom  = "Terraform"
      Repository    = "aws-data-streaming-app"
      RetentionDate = var.retention_date
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}