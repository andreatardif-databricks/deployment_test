terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

resource "databricks_notebook" "pipeline" {
  path     = "/Shared/teaching_strategies/teaching_strategies_pipeline"
  language = "PYTHON"
  source   = "${path.module}/notebooks/teaching_strategies_pipeline.py"
}

resource "databricks_pipeline" "this" {
  name       = "teaching_strategies_pipeline"
  serverless = true
  catalog    = var.catalog_name
  target     = "gold"

  library {
    notebook {
      path = databricks_notebook.pipeline.id
    }
  }
}
