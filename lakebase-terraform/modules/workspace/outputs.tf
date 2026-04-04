output "workspace_url" {
  description = "The URL of the created workspace"
  value       = databricks_mws_workspaces.this.workspace_url
}

output "workspace_id" {
  description = "The numeric ID of the workspace"
  value       = databricks_mws_workspaces.this.workspace_id
}

output "service_principal_app_id" {
  description = "Application ID of the service principal"
  value       = databricks_service_principal.this.application_id
}

output "service_principal_id" {
  description = "Internal ID of the service principal"
  value       = databricks_service_principal.this.id
}
