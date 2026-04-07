terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Create the Lakebase Postgres catalog via REST API
resource "null_resource" "lakebase_catalog" {
  triggers = {
    workspace_url = var.workspace_url
    catalog_name  = var.lakebase_catalog_name
    project_name  = var.lakebase_project_name
    profile       = var.account_profile
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../../scripts/create_lakebase_catalog.sh '${var.workspace_url}' '${var.lakebase_catalog_name}' '${var.lakebase_project_name}' 'production' 'databricks_postgres' '${var.account_profile}'"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "bash ${path.module}/../../scripts/create_lakebase_catalog.sh --delete '${self.triggers.workspace_url}' '${self.triggers.catalog_name}' '${self.triggers.profile}'"
  }
}

# Create synced tables via REST API
resource "null_resource" "synced_tables" {
  depends_on = [null_resource.lakebase_catalog]

  triggers = {
    workspace_url    = var.workspace_url
    lakebase_catalog = var.lakebase_catalog_name
    profile          = var.account_profile
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../../scripts/create_synced_tables.sh '${var.workspace_url}' '${var.catalog_name}' '${var.lakebase_catalog_name}' '${var.lakebase_project_uid}' '${var.lakebase_branch_id}' '${var.account_profile}'"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "bash ${path.module}/../../scripts/create_synced_tables.sh --delete '${self.triggers.workspace_url}' '${self.triggers.lakebase_catalog}' '${self.triggers.profile}'"
  }
}
