variable "workspace_url" {
  description = "Workspace URL for REST API calls"
  type        = string
}

variable "catalog_name" {
  description = "Source UC catalog with Gold tables"
  type        = string
}

variable "lakebase_catalog_name" {
  description = "Name for the Lakebase Postgres catalog"
  type        = string
}

variable "lakebase_project_name" {
  description = "Full resource name of the Lakebase project"
  type        = string
}

variable "lakebase_project_uid" {
  description = "Project UID (bare ID) for synced tables API"
  type        = string
}

variable "lakebase_branch_id" {
  description = "Production branch UID (bare ID) for synced tables API"
  type        = string
}

variable "account_profile" {
  description = "Databricks CLI profile for authentication"
  type        = string
}
