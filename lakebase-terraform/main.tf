# Phase 1: Workspace, metastore, service principal
module "workspace" {
  source = "./modules/workspace"

  providers = {
    databricks = databricks.account
  }

  account_id              = var.account_id
  workspace_name          = var.workspace_name
  aws_region              = var.aws_region
  metastore_id            = var.metastore_id
  service_principal_name  = var.service_principal_name
}

# Phase 2: Unity Catalog structure + data upload
module "unity_catalog" {
  source = "./modules/unity-catalog"

  providers = {
    databricks = databricks.workspace
  }

  catalog_name = var.catalog_name
  data_dir     = "${path.root}/data"

  depends_on = [module.workspace]
}

# Phase 3: SDP Pipeline
module "pipeline" {
  source = "./modules/pipeline"

  providers = {
    databricks = databricks.workspace
  }

  catalog_name = var.catalog_name

  depends_on = [module.unity_catalog]
}

# Phase 4: Lakebase Autoscaling
module "lakebase" {
  source = "./modules/lakebase"

  providers = {
    databricks = databricks.workspace
  }

  project_id = var.lakebase_project_id

  depends_on = [module.workspace]
}

# Phase 5: Synced tables (REST API)
module "sync" {
  source = "./modules/sync"

  providers = {
    databricks = databricks.workspace
  }

  workspace_url         = module.workspace.workspace_url
  catalog_name          = var.catalog_name
  lakebase_catalog_name = var.lakebase_catalog_name
  lakebase_project_name = module.lakebase.project_name
  lakebase_project_uid  = module.lakebase.project_uid
  lakebase_branch_id    = module.lakebase.production_branch_uid
  account_profile       = var.account_profile

  depends_on = [module.pipeline, module.lakebase]
}

# Phase 6: Permissions
module "permissions" {
  source = "./modules/permissions"

  providers = {
    databricks = databricks.workspace
  }

  catalog_name          = var.catalog_name
  lakebase_catalog_name = var.lakebase_catalog_name
  service_principal_id  = module.workspace.service_principal_app_id
  user_email            = var.user_email
  group_name            = var.group_name
  workspace_url         = module.workspace.workspace_url
  lakebase_project_name = module.lakebase.project_name
  account_profile       = var.account_profile

  depends_on = [module.sync]
}
