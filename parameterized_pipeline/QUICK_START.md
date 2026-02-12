# Quick Start Guide

This guide will help you get started with the parameterized pipeline bundle in 5 minutes.

## Choose Your Approach

This bundle provides **two ways** to configure your pipeline:

### Option 1: Simple Variables (Recommended for simple configs)
✅ Use when you have 3-5 configuration values  
✅ Good for: catalog, schema, table names  
✅ Example: Basic pipeline (`data_pipeline`)

### Option 2: External YAML Config Files (Recommended for complex configs)
✅ Use when you have many configuration values  
✅ Good for: Kafka settings, OAuth, checkpoints, secrets  
✅ Example: Config-based pipeline (`data_pipeline_with_config`)

## Getting Started with Simple Variables

### 1. Review databricks.yml

```yaml
variables:
  catalog: "main"
  schema: "default"
  pipeline_config: "dev"

targets:
  dev:
    variables:
      catalog: "andrea_tardif"
      schema: "bronze"
```

### 2. Deploy

```bash
databricks bundle deploy -t dev
```

### 3. Run

```bash
databricks bundle run data_pipeline -t dev
```

## Getting Started with YAML Config Files

### 1. Create/Edit Your Config File

Edit `config/dev_config.yml`:

```yaml
secrets:
  databricks_secret_scope: 'my-secret-scope'
  keyvault_url: 'https://my-keyvault.vault.azure.net/'

general:
  streaming:
    checkpoint_path: 'abfss://checkpoints@mystorage.dfs.core.windows.net'
    consumer_group_prefix: 'dev_'
  
  kafka:
    main:
      host: 'my-kafka-host.servicebus.windows.net'
      use_oauth: true
```

### 2. Deploy

```bash
databricks bundle deploy -t dev
```

### 3. Run

```bash
databricks bundle run data_pipeline_with_config -t dev
```

## Using Your Config in the Pipeline

In your notebook:

```python
from config_loader import ConfigLoader

# Load configuration
config_path = spark.conf.get("config_file_path")
config = ConfigLoader(config_path)

# Access values using dot notation
kafka_host = config.get('general.kafka.main.host')
checkpoint = config.get('general.streaming.checkpoint_path')

# Use in your DLT tables
@dlt.table(name="my_table")
def my_table():
    return (
        spark.range(100)
        .withColumn("kafka_host", F.lit(kafka_host))
    )
```

## Multiple Environments

The same pipeline works across all environments:

```bash
# Dev environment (uses config/dev_config.yml)
databricks bundle deploy -t dev
databricks bundle run data_pipeline_with_config -t dev

# Staging environment (uses config/ppe_config.yml)
databricks bundle deploy -t staging
databricks bundle run data_pipeline_with_config -t staging

# Production environment (uses config/prod_config.yml)
databricks bundle deploy -t prod
databricks bundle run data_pipeline_with_config -t prod
```

## File Structure

```
parameterized_pipeline/
├── databricks.yml                      # Main bundle configuration
├── config/                            # Your YAML config files
│   ├── dev_config.yml                # Development settings
│   ├── ppe_config.yml                # PPE/Staging settings
│   └── prod_config.yml               # Production settings
├── src/
│   ├── config_loader.py              # Helper to load configs
│   ├── pipeline.ipynb                # Basic pipeline
│   └── pipeline_with_config.ipynb    # Config-based pipeline
└── resources/
    └── pipeline.yml                  # Pipeline definitions
```

## Key Benefits

🎯 **One pipeline, multiple environments** - No duplication!  
📝 **External configs** - No hardcoded values  
🔒 **Secret management** - Reference secret scopes  
🚀 **Quick deployment** - Change configs without code changes  

## Next Steps

- **Simple configs**: Edit variables in `databricks.yml`
- **Complex configs**: Create/edit YAML files in `config/` directory
- **Full docs**: See [CONFIG_USAGE.md](./CONFIG_USAGE.md)
- **Customize**: Modify the notebooks in `src/` for your use case

## Common Tasks

### Add a new environment

1. Add target in `databricks.yml`:
```yaml
targets:
  uat:
    variables:
      config_file_path: "../config/uat_config.yml"
```

2. Create `config/uat_config.yml`

3. Deploy:
```bash
databricks bundle deploy -t uat
```

### Add new config values

1. Add to your YAML file:
```yaml
general:
  my_new_setting: "value"
```

2. Access in notebook:
```python
my_value = config.get('general.my_new_setting')
```

### Use secrets

1. Store secret in Databricks Secret Scope

2. Reference in config:
```yaml
general:
  my_service:
    api_key_vault_key: 'my-api-key'
```

3. Retrieve in notebook:
```python
api_key = config.get_secret_from_scope('my-api-key')
```

## Need Help?

- Review [CONFIG_USAGE.md](./CONFIG_USAGE.md) for detailed examples
- Check [README.md](./README.md) for architecture overview
- Look at example notebooks in `src/` directory
