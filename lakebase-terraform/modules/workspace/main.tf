terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Create serverless workspace
resource "databricks_mws_workspaces" "this" {
  account_id     = var.account_id
  workspace_name = var.workspace_name
  aws_region     = var.aws_region
  compute_mode   = "SERVERLESS"
}

# Wait for workspace to be ready
resource "time_sleep" "workspace_ready" {
  depends_on      = [databricks_mws_workspaces.this]
  create_duration = "120s"
}

# Assign metastore to the new workspace
resource "databricks_metastore_assignment" "this" {
  workspace_id = databricks_mws_workspaces.this.workspace_id
  metastore_id = var.metastore_id

  depends_on = [time_sleep.workspace_ready]
}

# Create service principal
resource "databricks_service_principal" "this" {
  display_name = var.service_principal_name
  active       = true

  depends_on = [time_sleep.workspace_ready]
}
