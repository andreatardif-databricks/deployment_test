terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# NOTE: lakebase-users group must be created at account level before applying.
# databricks account groups create --display-name lakebase-users --profile one-env-account

# --- Unity Catalog Grants ---

# Catalog: teaching_strategies
resource "databricks_grants" "catalog" {
  catalog = var.catalog_name

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.group_name
    privileges = ["USE_CATALOG"]
  }
}

# Schema: bronze
resource "databricks_grants" "bronze" {
  schema = "${var.catalog_name}.bronze"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.group_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# Schema: silver
resource "databricks_grants" "silver" {
  schema = "${var.catalog_name}.silver"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.group_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# Schema: gold
resource "databricks_grants" "gold" {
  schema = "${var.catalog_name}.gold"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.group_name
    privileges = ["USE_SCHEMA", "SELECT"]
  }
}

# Volume: raw_data
resource "databricks_grants" "volume" {
  volume = "${var.catalog_name}.bronze.raw_data"

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.group_name
    privileges = ["READ_VOLUME"]
  }
}

# Catalog: teaching_strategies_pg (Lakebase Postgres)
resource "databricks_grants" "lakebase_catalog" {
  catalog = var.lakebase_catalog_name

  grant {
    principal  = var.service_principal_id
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.user_email
    privileges = ["ALL_PRIVILEGES"]
  }
  grant {
    principal  = var.group_name
    privileges = ["USE_CATALOG"]
  }
}

# --- Lakebase Project Permissions (REST API) ---

resource "null_resource" "lakebase_project_perms" {
  triggers = {
    workspace_url = var.workspace_url
    project_name  = var.lakebase_project_name
  }

  provisioner "local-exec" {
    command = "bash ${path.module}/../../scripts/manage_lakebase_perms.sh '${var.workspace_url}' '${var.lakebase_project_name}' '${var.service_principal_id}' '${var.user_email}' '${var.group_name}' '${var.account_profile}'"
  }
}
