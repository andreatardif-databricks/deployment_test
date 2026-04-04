terraform {
  required_version = ">= 1.5.0"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.65.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">= 3.0"
    }
    time = {
      source  = "hashicorp/time"
      version = ">= 0.9"
    }
  }
}

# Account-level provider (workspace creation, metastore assignment)
provider "databricks" {
  alias      = "account"
  host       = "https://accounts.cloud.databricks.com"
  account_id = var.account_id
  auth_type  = "databricks-cli"
  profile    = var.account_profile
}

# Workspace-level provider (UC, pipeline, Lakebase, permissions)
provider "databricks" {
  alias     = "workspace"
  host      = module.workspace.workspace_url
  auth_type = "databricks-cli"
  profile   = var.account_profile
}
