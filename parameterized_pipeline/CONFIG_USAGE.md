# Using External YAML Configuration Files in DLT Pipelines

This guide explains how to use external YAML configuration files in your Delta Live Tables (DLT) pipelines to avoid hardcoding configuration values and to support multiple environments without duplicating pipeline definitions.

## Overview

The bundle includes two approaches:

1. **Basic Pipeline** (`data_pipeline`): Uses simple variables from `databricks.yml`
2. **Config-Based Pipeline** (`data_pipeline_with_config`): Loads configuration from external YAML files

## Directory Structure

```
parameterized_pipeline/
├── databricks.yml                          # Main bundle config
├── config/                                 # Configuration files directory
│   ├── dev_config.yml                     # Development environment config
│   ├── ppe_config.yml                     # PPE environment config (customer sample)
│   └── prod_config.yml                    # Production environment config
├── src/
│   ├── config_loader.py                   # Helper module to load YAML configs
│   ├── pipeline.ipynb                     # Basic pipeline
│   ├── pipeline_with_config.ipynb         # Pipeline using external config
│   └── requirements.txt                   # Python dependencies
└── resources/
    └── pipeline.yml                       # Pipeline definitions
```

## Configuration File Format

Your YAML configuration files can have any structure you need. Here's the example based on your customer's format:

```yaml
secrets:
  databricks_secret_scope: 'eshareanalyticsppe-keyvault'
  keyvault_url: 'https://analyticsppe-keyvault.vault.azure.net/'

general:
  dead_letter_queue:
    kafka: null
    topic: 'dead_letter_queue'
  
  streaming:
    checkpoint_path: 'abfss://spark-streaming-checkpoint@storage.dfs.core.windows.net'
    consumer_group_prefix: 'ppe_'
    fail_on_missed_kafka_records: false
  
  schema_service:
    schema_service_url: 'http://api.analytics.ppe.int.e-share.us'
  
  kafka:
    main:
      host: 'eventhubs.servicebus.windows.net'
      use_oauth: true
  
  kafka_oauth:
    client_id: '1c904a1e-fb60-4adf-849c-289dce766f19'
    client_secret_vault_key: 'service-principal-etl-client-secret'
    token_url: 'https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token'
```

## How It Works

### Step 1: Define Config Path in databricks.yml

```yaml
variables:
  config_file_path:
    description: "Path to the YAML configuration file"
    default: "../config/dev_config.yml"

targets:
  dev:
    variables:
      config_file_path: "../config/dev_config.yml"
  
  staging:
    variables:
      config_file_path: "../config/ppe_config.yml"
```

### Step 2: Pass Config Path in pipeline.yml

```yaml
resources:
  pipelines:
    data_pipeline_with_config:
      configuration:
        config_file_path: ${var.config_file_path}
      
      libraries:
        - notebook:
            path: ../src/pipeline_with_config.ipynb
        - file:
            path: ../src/config_loader.py
```

### Step 3: Load Config in Your Pipeline Notebook

```python
from config_loader import ConfigLoader

# Get config file path from pipeline settings
config_file_path = spark.conf.get("config_file_path", "../config/dev_config.yml")

# Load the configuration
config = ConfigLoader(config_file_path)

# Access configuration values using dot notation
kafka_host = config.get('general.kafka.main.host')
checkpoint_path = config.get('general.streaming.checkpoint_path')
secret_scope = config.get('secrets.databricks_secret_scope')
```

## Using the ConfigLoader

The `ConfigLoader` class provides several convenient methods:

### Basic Usage

```python
# Initialize with config file path
config = ConfigLoader('../config/ppe_config.yml')

# Get values using dot notation
value = config.get('general.kafka.main.host')

# Get with default value
value = config.get('some.key.that.might.not.exist', default='default_value')
```

### Accessing Specific Sections

```python
# Get entire sections
secrets = config.get_secrets()
general = config.get_general()
kafka_config = config.get_kafka_config()
streaming_config = config.get_streaming_config()
```

### Retrieving Secrets from Databricks Secret Scope

```python
# Get secret from Databricks Secret Scope
secret_key_name = config.get('general.kafka_oauth.client_secret_vault_key')
client_secret = config.get_secret_from_scope(secret_key_name)
```

### Display Configuration

```python
# Display config (masks secrets by default)
config.display_config(mask_secrets=True)
```

## Using Config Values in DLT Tables

You can use configuration values in your DLT table definitions:

```python
@dlt.table(
    name="my_table",
    table_properties={
        "kafka_host": config.get('general.kafka.main.host'),
        "environment": config.get('general.streaming.consumer_group_prefix')
    }
)
def my_table():
    checkpoint_path = config.get('general.streaming.checkpoint_path')
    kafka_host = config.get('general.kafka.main.host')
    
    return (
        spark.range(100)
        .withColumn("kafka_host", F.lit(kafka_host))
        .withColumn("checkpoint_path", F.lit(checkpoint_path))
    )
```

## Deployment

Deploy to different environments using different config files:

```bash
# Deploy to dev (uses dev_config.yml)
databricks bundle deploy -t dev

# Deploy to staging (uses ppe_config.yml)
databricks bundle deploy -t staging

# Deploy to prod (uses prod_config.yml)
databricks bundle deploy -t prod
```

## Running the Pipelines

```bash
# Run the basic pipeline
databricks bundle run data_pipeline -t dev

# Run the config-based pipeline
databricks bundle run data_pipeline_with_config -t dev
```

## Benefits

✅ **No Hardcoding**: All environment-specific values in external files  
✅ **Single Pipeline Definition**: One pipeline works for all environments  
✅ **Easy Updates**: Change config without modifying pipeline code  
✅ **Version Control**: Track configuration changes separately  
✅ **Security**: Sensitive values can reference secret scopes  
✅ **Flexibility**: Support any YAML structure you need  

## Best Practices

1. **Keep secrets in Secret Scopes**: Don't put actual secrets in config files, use secret scope keys
2. **Version your configs**: Commit config files to git for change tracking
3. **Validate configs**: Test config files before deploying
4. **Document structure**: Add comments in your YAML files to explain each section
5. **Use sensible defaults**: Provide default values in `config.get()` calls
6. **Separate environments**: Use different config files for dev/staging/prod

## Example: Kafka Streaming with Config

Here's a complete example using Kafka configuration:

```python
from config_loader import ConfigLoader
import dlt
from pyspark.sql import functions as F

# Load configuration
config_file_path = spark.conf.get("config_file_path")
config = ConfigLoader(config_file_path)

# Get Kafka configuration
kafka_host = config.get('general.kafka.main.host')
use_oauth = config.get('general.kafka.main.use_oauth')
checkpoint_path = config.get('general.streaming.checkpoint_path')
consumer_group_prefix = config.get('general.streaming.consumer_group_prefix')

# Get OAuth configuration if needed
if use_oauth:
    client_id = config.get('general.kafka_oauth.client_id')
    client_secret_key = config.get('general.kafka_oauth.client_secret_vault_key')
    client_secret = config.get_secret_from_scope(client_secret_key)
    token_url = config.get('general.kafka_oauth.token_url')

@dlt.table(name="kafka_stream")
def stream_from_kafka():
    return (
        spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_host)
            .option("subscribe", "my_topic")
            .option("startingOffsets", "latest")
            .load()
            .select(
                F.col("value").cast("string").alias("message"),
                F.col("timestamp")
            )
    )
```

## Troubleshooting

### Config file not found
- Check the path in `databricks.yml` is relative to the notebook location
- Verify the config file exists in the `config/` directory

### YAML parsing errors
- Validate your YAML syntax using an online YAML validator
- Check for proper indentation (use spaces, not tabs)

### Can't access secrets
- Verify the secret scope exists in your workspace
- Check you have permissions to access the secret scope
- Ensure the secret key exists in the scope

## Next Steps

1. Create your own config files based on your requirements
2. Update the pipeline notebook to use your specific configuration values
3. Test with dev environment first
4. Add more environments as needed
