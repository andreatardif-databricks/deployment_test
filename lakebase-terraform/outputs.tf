output "workspace_url" {
  description = "URL of the new serverless workspace"
  value       = module.workspace.workspace_url
}

output "workspace_id" {
  description = "ID of the new workspace"
  value       = module.workspace.workspace_id
}

output "service_principal_app_id" {
  description = "Application ID of the service principal"
  value       = module.workspace.service_principal_app_id
}

output "lakebase_project_name" {
  description = "Lakebase project resource name"
  value       = module.lakebase.project_name
}

output "lakebase_production_endpoint" {
  description = "Production branch endpoint host"
  value       = module.lakebase.production_endpoint_host
}

output "lakebase_dev_endpoint" {
  description = "Development branch endpoint host"
  value       = module.lakebase.dev_endpoint_host
}
