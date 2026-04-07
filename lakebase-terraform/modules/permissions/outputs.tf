output "group_name" {
  description = "Name of the lakebase-users group"
  value       = var.group_name
}

output "permissions_applied" {
  description = "Whether all permissions were applied"
  value       = true
  depends_on  = [null_resource.lakebase_project_perms]
}
