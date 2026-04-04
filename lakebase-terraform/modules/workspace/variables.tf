variable "account_id" {
  description = "Databricks account ID"
  type        = string
}

variable "workspace_name" {
  description = "Name for the serverless workspace"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "metastore_id" {
  description = "Metastore ID to assign to the workspace"
  type        = string
}

variable "service_principal_name" {
  description = "Display name for the service principal"
  type        = string
}
