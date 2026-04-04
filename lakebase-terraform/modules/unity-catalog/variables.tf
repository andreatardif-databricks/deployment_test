variable "catalog_name" {
  description = "Name of the Unity Catalog catalog"
  type        = string
}

variable "data_dir" {
  description = "Local directory containing CSV data files"
  type        = string
}

variable "workspace_profile" {
  description = "Databricks CLI profile for workspace-level access"
  type        = string
}
