variable "account_id" {
  description = "Databricks account ID"
  type        = string
  default     = "0d26daa6-5e44-4c97-a497-ef015f91254a"
}

variable "account_profile" {
  description = "Databricks CLI profile for account-level OAuth"
  type        = string
  default     = "one-env-account"
}

variable "workspace_name" {
  description = "Name for the new serverless workspace"
  type        = string
  default     = "lakebase-terraform-ws"
}

variable "aws_region" {
  description = "AWS region for the workspace"
  type        = string
  default     = "us-east-1"
}

variable "metastore_id" {
  description = "ID of existing metastore to assign"
  type        = string
  default     = "cc9be128-0493-426b-8d96-68d98d08517b"
}

variable "catalog_name" {
  description = "Unity Catalog catalog name"
  type        = string
  default     = "teaching_strategies"
}

variable "lakebase_project_id" {
  description = "Lakebase Autoscaling project ID"
  type        = string
  default     = "teaching-strategies-project"
}

variable "lakebase_catalog_name" {
  description = "Name for the Lakebase Postgres UC catalog"
  type        = string
  default     = "teaching_strategies_pg"
}

variable "user_email" {
  description = "Primary user email for permissions"
  type        = string
  default     = "andrea.tardif@databricks.com"
}

variable "service_principal_name" {
  description = "Display name for the service principal"
  type        = string
  default     = "lakebase-terraform-sp"
}

variable "group_name" {
  description = "Group name for Lakebase users"
  type        = string
  default     = "lakebase-users"
}
