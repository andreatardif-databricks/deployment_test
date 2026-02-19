# Parameterized Pipeline Bundle

This DABs bundle demonstrates how to create a parameterized Delta Live Tables (DLT) pipeline that uses configuration files to avoid duplicating pipeline definitions across environments.

## Key Features

- **Single Pipeline Definition**: One pipeline definition works for dev, staging, and prod
- **Configuration-Driven**: Uses YAML configuration files to parameterize the pipeline
- **Environment Variables**: Different configurations per target environment
- **No Duplication**: Same pipeline code works for all environments with different configs

## Architecture

The bundle uses a two-file YAML approach:

1. **`databricks.yml`**: Defines configuration parameters and variables for different environments
2. **`resources/pipeline.yml`**: Single pipeline definition that references configuration variables from databricks.yml

## Structure

```
parameterized_pipeline/
├── databricks.yml                    # Configuration file with variables
├── resources/
│   └── pipeline.yml                 # Pipeline definition (uses variables)
├── src/
│   └── pipeline.ipynb               # DLT pipeline notebook
└── README.md
```

## How It Works

### Variables in databricks.yml

The main bundle file defines variables that can be overridden per target:

```yaml
variables:
  catalog: "main"
  schema: "default"
  source_table: "raw_data"
  target_table: "processed_data"
  pipeline_config: "dev"
```

### Pipeline Configuration

The pipeline references these variables in `resources/pipeline.yml`:

```yaml
resources:
  pipelines:
    data_pipeline:
      target: ${var.catalog}.${var.schema}
      configuration:
        catalog: ${var.catalog}
        schema: ${var.schema}
        source_table: ${var.source_table}
        target_table: ${var.target_table}
        pipeline_config: ${var.pipeline_config}
```

### Target Environments

Each target (dev, staging, prod) overrides the variables:

```yaml
targets:
  dev:
    variables:
      catalog: "andrea_tardif"
      schema: "bronze"
      pipeline_config: "dev"
  
  staging:
    variables:
      catalog: "andrea_tardif"
      schema: "silver"
      pipeline_config: "staging"
```

## Usage

### Deploy to Development

```bash
databricks bundle deploy -t dev
```

### Deploy to Staging

```bash
databricks bundle deploy -t staging
```

### Deploy to Production

```bash
databricks bundle deploy -t prod
```

### Run the Pipeline

```bash
# Run in dev environment
databricks bundle run data_pipeline -t dev

# Run in staging environment
databricks bundle run data_pipeline -t staging

# Run in prod environment
databricks bundle run data_pipeline -t prod
```

## Pipeline Overview

The pipeline implements a medallion architecture with three layers:

1. **Bronze Layer** (`raw_data`): Ingests raw data
2. **Silver Layer** (`processed_data`): Applies data quality checks and transformations
3. **Gold Layer** (`aggregated_data`): Creates business-ready aggregated metrics

### Data Quality Checks

The pipeline includes expectations that drop invalid records:
- `valid_id`: Ensures ID is not null
- `valid_value`: Ensures value is non-negative

## Customization

### Adding New Environments

To add a new environment, add a new target in `databricks.yml`:

```yaml
targets:
  custom_env:
    mode: development
    workspace:
      host: https://your-workspace.cloud.databricks.com
    variables:
      catalog: "your_catalog"
      schema: "your_schema"
      pipeline_config: "custom"
```

### Adding More Configuration Parameters

1. Add the variable to the `variables` section in `databricks.yml`
2. Reference it in `resources/pipeline.yml` configuration
3. Use it in your pipeline notebook via `spark.conf.get()`

## Benefits

✅ **No Duplication**: Single pipeline definition for all environments  
✅ **Easy Configuration**: Change variables without modifying pipeline code  
✅ **Environment Isolation**: Each target has its own catalog/schema  
✅ **Scalable**: Easy to add new environments or configuration parameters  
✅ **Type Safety**: Variables are defined centrally with defaults  

## Using External YAML Configuration Files

This bundle includes support for external YAML configuration files! This allows you to store complex configuration (like Kafka settings, OAuth credentials, checkpoint paths, etc.) in separate YAML files.

### Two Pipeline Options:

1. **`data_pipeline`**: Basic pipeline using simple variables
2. **`data_pipeline_with_config`**: Pipeline that loads configuration from external YAML files

### Configuration Files:

- `config/dev_config.yml` - Development environment
- `config/ppe_config.yml` - PPE environment (customer sample)
- `config/prod_config.yml` - Production environment

**📖 See [CONFIG_USAGE.md](./CONFIG_USAGE.md) for complete documentation on using external config files.**

### Quick Example:

```python
from config_loader import ConfigLoader

# Load config from file path passed by DABs bundle
config_file_path = spark.conf.get("config_file_path")
config = ConfigLoader(config_file_path)

# Access any configuration value using dot notation
kafka_host = config.get('general.kafka.main.host')
checkpoint_path = config.get('general.streaming.checkpoint_path')
secret_scope = config.get('secrets.databricks_secret_scope')
```

## Next Steps

- Review the [CONFIG_USAGE.md](./CONFIG_USAGE.md) guide for detailed examples
- Modify the pipeline notebook to process your actual data sources
- Create your own config files based on your requirements
- Add more configuration parameters as needed
- Customize the data quality expectations
- Add more layers or transformations to the pipeline
