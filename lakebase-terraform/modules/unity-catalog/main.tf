terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

# Catalog
resource "databricks_catalog" "this" {
  name    = var.catalog_name
  comment = "Teaching Strategies education domain data"
}

# Schemas
resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.this.name
  name         = "bronze"
  comment      = "Raw ingestion layer"
}

resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.this.name
  name         = "silver"
  comment      = "Cleaned and deduplicated data"
}

resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.this.name
  name         = "gold"
  comment      = "Business-ready aggregations"
}

# Volume for raw data landing
resource "databricks_volume" "raw_data" {
  catalog_name = databricks_catalog.this.name
  schema_name  = databricks_schema.bronze.name
  name         = "raw_data"
  volume_type  = "MANAGED"
  comment      = "Raw CSV data landing zone"
}

# Upload CSVs to volume
resource "null_resource" "upload_data" {
  depends_on = [databricks_volume.raw_data]

  triggers = {
    data_dir = var.data_dir
  }

  provisioner "local-exec" {
    command = <<-EOT
      for csv_file in ${var.data_dir}/*.csv; do
        if [ -f "$csv_file" ]; then
          filename=$(basename "$csv_file")
          databricks fs cp "$csv_file" \
            "dbfs:/Volumes/${var.catalog_name}/bronze/raw_data/$filename" \
            --overwrite
        fi
      done
    EOT
  }
}
