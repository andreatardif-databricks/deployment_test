variable "catalog_name" {
  description = "Unity Catalog catalog name"
  type        = string
}

variable "lakebase_catalog_name" {
  description = "Lakebase Postgres catalog name"
  type        = string
}

variable "service_principal_id" {
  description = "Service principal application ID"
  type        = string
}

variable "user_email" {
  description = "User email for permissions"
  type        = string
}

variable "group_name" {
  description = "Group name for Lakebase users"
  type        = string
}

variable "workspace_url" {
  description = "Workspace URL for REST API calls"
  type        = string
}

variable "lakebase_project_name" {
  description = "Full resource name of the Lakebase project"
  type        = string
}

variable "account_profile" {
  description = "Databricks CLI profile"
  type        = string
}
