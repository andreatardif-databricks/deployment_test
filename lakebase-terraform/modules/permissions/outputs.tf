output "group_id" {
  description = "ID of the lakebase-users group"
  value       = databricks_group.lakebase_users.id
}

output "permissions_applied" {
  description = "Whether all permissions were applied"
  value       = true
  depends_on  = [null_resource.lakebase_project_perms]
}
