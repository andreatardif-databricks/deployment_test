output "lakebase_catalog_created" {
  description = "Whether the Lakebase catalog was created"
  value       = true
  depends_on  = [null_resource.lakebase_catalog]
}

output "synced_tables_created" {
  description = "Whether synced tables were created"
  value       = true
  depends_on  = [null_resource.synced_tables]
}
