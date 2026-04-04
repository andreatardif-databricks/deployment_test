terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Lakebase Autoscaling Project
resource "databricks_postgres_project" "this" {
  project_id = var.project_id
  spec = {
    pg_version   = 17
    display_name = "Teaching Strategies Lakebase"
    default_endpoint_settings = {
      autoscaling_limit_min_cu = 0.5
      autoscaling_limit_max_cu = 4.0
      suspend_timeout_duration = "300s"
    }
  }
}

# Production branch (default, created with project — import or manage explicitly)
# The default production branch + endpoint are auto-created with the project.
# We manage additional branches here.

# Development branch
resource "databricks_postgres_branch" "development" {
  branch_id = "development"
  parent    = databricks_postgres_project.this.name
  spec = {
    ttl = "604800s" # 7 days
  }
}

# Development endpoint
resource "databricks_postgres_endpoint" "dev_primary" {
  endpoint_id = "ep-dev-primary"
  parent      = databricks_postgres_branch.development.name
  spec = {
    endpoint_type = "ENDPOINT_TYPE_READ_WRITE"
  }
}

# Data sources to read auto-created production resources
data "databricks_postgres_endpoints" "production" {
  parent = "${databricks_postgres_project.this.name}/branches/production"
}
