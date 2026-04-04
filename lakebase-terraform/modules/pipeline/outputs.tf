output "pipeline_id" {
  description = "ID of the SDP pipeline"
  value       = databricks_pipeline.this.id
}

output "pipeline_name" {
  description = "Name of the SDP pipeline"
  value       = databricks_pipeline.this.name
}
