# Examples: Using YAML Config in Your Pipeline

This document provides practical examples of using external YAML configuration files in your DLT pipeline.

## Example 1: Basic Configuration Access

```python
from config_loader import ConfigLoader
import dlt
from pyspark.sql import functions as F

# Load configuration
config_path = spark.conf.get("config_file_path")
config = ConfigLoader(config_path)

# Access simple values
kafka_host = config.get('general.kafka.main.host')
checkpoint_path = config.get('general.streaming.checkpoint_path')

print(f"Kafka Host: {kafka_host}")
print(f"Checkpoint: {checkpoint_path}")
```

## Example 2: Using Config in DLT Tables

```python
# Get configuration values
kafka_host = config.get('general.kafka.main.host')
consumer_group_prefix = config.get('general.streaming.consumer_group_prefix')

@dlt.table(
    name="events",
    comment="Event stream from Kafka",
    table_properties={
        "kafka_host": kafka_host,
        "quality": "bronze"
    }
)
def events_table():
    return (
        spark.range(1000)
        .withColumn("event_id", F.col("id"))
        .withColumn("kafka_source", F.lit(kafka_host))
        .withColumn("consumer_group", F.lit(consumer_group_prefix))
        .withColumn("timestamp", F.current_timestamp())
    )
```

## Example 3: OAuth Configuration

```python
# Get OAuth settings
use_oauth = config.get('general.kafka.main.use_oauth')

if use_oauth:
    client_id = config.get('general.kafka_oauth.client_id')
    token_url = config.get('general.kafka_oauth.token_url')
    secret_key = config.get('general.kafka_oauth.client_secret_vault_key')
    
    # Retrieve secret from Databricks Secret Scope
    client_secret = config.get_secret_from_scope(secret_key)
    
    print(f"OAuth Client ID: {client_id}")
    print(f"Token URL: {token_url}")
    # Note: Don't print the actual secret!
```

## Example 4: Kafka Streaming with Config

```python
from config_loader import ConfigLoader
import dlt
from pyspark.sql import functions as F

# Load configuration
config_path = spark.conf.get("config_file_path")
config = ConfigLoader(config_path)

# Get Kafka configuration
kafka_config = config.get_kafka_config()
kafka_host = config.get('general.kafka.main.host')
checkpoint_path = config.get('general.streaming.checkpoint_path')

@dlt.table(
    name="kafka_raw_stream",
    comment="Raw Kafka stream",
    table_properties={
        "quality": "bronze",
        "kafka_host": kafka_host
    }
)
def kafka_stream():
    return (
        spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_host)
            .option("subscribe", "my_topic")
            .option("startingOffsets", "latest")
            .load()
            .select(
                F.col("key").cast("string"),
                F.col("value").cast("string"),
                F.col("topic"),
                F.col("partition"),
                F.col("offset"),
                F.col("timestamp")
            )
    )
```

## Example 5: Multi-Environment Configuration

### Config File: config/dev_config.yml
```yaml
general:
  database:
    host: "dev-database.company.com"
    port: 5432
    name: "dev_db"
  
  api:
    endpoint: "https://api.dev.company.com"
    timeout: 30
```

### Config File: config/prod_config.yml
```yaml
general:
  database:
    host: "prod-database.company.com"
    port: 5432
    name: "prod_db"
  
  api:
    endpoint: "https://api.company.com"
    timeout: 10
```

### Pipeline Notebook
```python
# Same code works in both dev and prod!
config = ConfigLoader(spark.conf.get("config_file_path"))

db_host = config.get('general.database.host')
db_port = config.get('general.database.port')
api_endpoint = config.get('general.api.endpoint')

@dlt.table(name="external_data")
def load_external_data():
    # Connect to database using config
    jdbc_url = f"jdbc:postgresql://{db_host}:{db_port}/{db_name}"
    
    return (
        spark.read
            .format("jdbc")
            .option("url", jdbc_url)
            .option("dbtable", "source_table")
            .load()
    )
```

## Example 6: Dead Letter Queue Pattern

```python
config = ConfigLoader(spark.conf.get("config_file_path"))

# Get DLQ configuration
dlq_topic = config.get('general.dead_letter_queue.topic')
kafka_host = config.get('general.kafka.main.host')

@dlt.table(
    name="processed_events",
    comment="Successfully processed events"
)
@dlt.expect_or_drop("valid_schema", "schema_version IS NOT NULL")
def processed_events():
    return dlt.read("raw_events")

@dlt.table(
    name="failed_events",
    comment="Events that failed processing (Dead Letter Queue)"
)
def failed_events():
    # Events that fail validation go here
    return (
        dlt.read("raw_events")
        .where("schema_version IS NULL")
        .withColumn("failure_reason", F.lit("Invalid schema"))
        .withColumn("dlq_topic", F.lit(dlq_topic))
        .withColumn("retry_count", F.lit(0))
    )
```

## Example 7: Configuration Validation

```python
from config_loader import ConfigLoader

config = ConfigLoader(spark.conf.get("config_file_path"))

# Validate required configuration exists
required_configs = [
    'general.kafka.main.host',
    'general.streaming.checkpoint_path',
    'secrets.databricks_secret_scope'
]

print("Validating configuration...")
for config_key in required_configs:
    value = config.get(config_key)
    if value is None:
        raise ValueError(f"Required configuration missing: {config_key}")
    print(f"✓ {config_key}: {value}")

print("✓ All required configurations present")
```

## Example 8: Dynamic Table Names from Config

```python
config = ConfigLoader(spark.conf.get("config_file_path"))

# Get table name prefix from config
table_prefix = config.get('general.table_prefix', 'default')

@dlt.table(
    name=f"{table_prefix}_bronze_events",
    comment="Bronze layer events"
)
def bronze_events():
    return spark.range(100)

@dlt.table(
    name=f"{table_prefix}_silver_events",
    comment="Silver layer events"
)
def silver_events():
    return dlt.read(f"{table_prefix}_bronze_events")
```

## Example 9: Schema Service Integration

```python
import requests
from config_loader import ConfigLoader

config = ConfigLoader(spark.conf.get("config_file_path"))

# Get schema service configuration
schema_service_url = config.get('general.schema_service.schema_service_url')
basic_auth_username = config.get('general.schema_service.schema_service_basic_auth_username')

# Get password from secret scope if configured
password_key = config.get('general.schema_service.schema_service_basic_auth_password_vault_key')
if password_key:
    password = config.get_secret_from_scope(password_key)
    auth = (basic_auth_username, password)
else:
    auth = None

def get_schema(schema_id: str):
    """Fetch schema from schema service"""
    url = f"{schema_service_url}/schemas/{schema_id}"
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    return response.json()

# Use in pipeline
@dlt.table(name="validated_events")
def validated_events():
    # Fetch schema and validate events
    schema = get_schema("event_schema_v1")
    return dlt.read("raw_events")  # Add validation logic here
```

## Example 10: Complete Real-World Example

```python
from config_loader import ConfigLoader
import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Initialize configuration
config_path = spark.conf.get("config_file_path")
config = ConfigLoader(config_path)

# Display configuration (masked)
config.display_config(mask_secrets=True)

# Get all required configuration values
kafka_host = config.get('general.kafka.main.host')
use_oauth = config.get('general.kafka.main.use_oauth')
checkpoint_path = config.get('general.streaming.checkpoint_path')
consumer_group_prefix = config.get('general.streaming.consumer_group_prefix')
dlq_topic = config.get('general.dead_letter_queue.topic')
secret_scope = config.get('secrets.databricks_secret_scope')

# OAuth configuration
if use_oauth:
    client_id = config.get('general.kafka_oauth.client_id')
    token_url = config.get('general.kafka_oauth.token_url')
    secret_key = config.get('general.kafka_oauth.client_secret_vault_key')
    client_secret = config.get_secret_from_scope(secret_key)

# Bronze Layer - Raw Ingestion
@dlt.table(
    name="bronze_kafka_events",
    comment="Raw Kafka events from bronze layer",
    table_properties={
        "quality": "bronze",
        "kafka_host": kafka_host,
        "pipeline_config": spark.conf.get("pipeline_config")
    }
)
def bronze_kafka_events():
    """Ingest raw events from Kafka"""
    return (
        spark.readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", kafka_host)
            .option("subscribe", "events")
            .option("startingOffsets", "latest")
            .option("kafka.group.id", f"{consumer_group_prefix}bronze_reader")
            .load()
            .select(
                F.col("key").cast("string").alias("event_key"),
                F.col("value").cast("string").alias("event_value"),
                F.col("topic").alias("source_topic"),
                F.col("partition").alias("source_partition"),
                F.col("offset").alias("source_offset"),
                F.col("timestamp").alias("event_timestamp"),
                F.current_timestamp().alias("ingestion_timestamp")
            )
    )

# Silver Layer - Parsed and Validated
@dlt.table(
    name="silver_events",
    comment="Parsed and validated events",
    table_properties={"quality": "silver"}
)
@dlt.expect_or_drop("valid_json", "event_json IS NOT NULL")
@dlt.expect_or_drop("has_id", "event_id IS NOT NULL")
def silver_events():
    """Parse JSON and validate events"""
    return (
        dlt.read_stream("bronze_kafka_events")
            .withColumn("event_json", F.from_json(F.col("event_value"), "id STRING, data STRING, timestamp TIMESTAMP"))
            .select(
                F.col("event_key"),
                F.col("event_json.id").alias("event_id"),
                F.col("event_json.data").alias("event_data"),
                F.col("event_json.timestamp").alias("event_timestamp"),
                F.col("ingestion_timestamp")
            )
    )

# Gold Layer - Business Metrics
@dlt.table(
    name="gold_event_metrics",
    comment="Aggregated event metrics by hour",
    table_properties={"quality": "gold"}
)
def gold_event_metrics():
    """Aggregate events by hour"""
    return (
        dlt.read("silver_events")
            .withColumn("hour", F.date_trunc("hour", F.col("event_timestamp")))
            .groupBy("hour")
            .agg(
                F.count("*").alias("event_count"),
                F.countDistinct("event_id").alias("unique_events"),
                F.min("event_timestamp").alias("first_event"),
                F.max("event_timestamp").alias("last_event")
            )
    )

# Dead Letter Queue
@dlt.table(
    name="dlq_failed_events",
    comment="Events that failed processing",
    table_properties={
        "quality": "quarantine",
        "dlq_topic": dlq_topic
    }
)
def dlq_failed_events():
    """Capture failed events for retry"""
    return (
        dlt.read_stream("bronze_kafka_events")
            .withColumn("parsed", F.from_json(F.col("event_value"), "id STRING, data STRING"))
            .where(F.col("parsed").isNull())
            .select(
                F.col("event_key"),
                F.col("event_value").alias("raw_value"),
                F.lit("JSON parsing failed").alias("failure_reason"),
                F.current_timestamp().alias("failed_at"),
                F.lit(dlq_topic).alias("target_dlq_topic")
            )
    )
```

## Key Takeaways

1. ✅ **Load config once** at the start of your notebook
2. ✅ **Extract all needed values** before defining DLT tables
3. ✅ **Use `config.get()`** with dot notation for nested values
4. ✅ **Retrieve secrets** from Secret Scope, don't hardcode
5. ✅ **Validate configuration** before processing
6. ✅ **Add config to table properties** for documentation
7. ✅ **Test with dev config** before deploying to prod
