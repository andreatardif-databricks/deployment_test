output "project_name" {
  description = "Full resource name of the project"
  value       = databricks_postgres_project.this.name
}

output "project_uid" {
  description = "Project UID (for REST API calls)"
  value       = databricks_postgres_project.this.uid
}

output "production_branch_uid" {
  description = "Production branch UID"
  value       = try(data.databricks_postgres_endpoints.production.endpoints[0].name, "")
}

output "dev_branch_name" {
  description = "Development branch resource name"
  value       = databricks_postgres_branch.development.name
}

output "production_endpoint_host" {
  description = "Production endpoint host"
  value       = try(data.databricks_postgres_endpoints.production.endpoints[0].status.hosts.host, "pending")
}

output "dev_endpoint_host" {
  description = "Development endpoint host"
  value       = try(data.databricks_postgres_endpoints.development.endpoints[0].status.hosts.host, "pending")
}
