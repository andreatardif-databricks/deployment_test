# Kafka Alerting Pipeline - Databricks Asset Bundle

A robust, production-ready DLT (Delta Live Tables) pipeline that ingests data from Kafka streams, processes data per client into Bronze/Silver/Gold layers, and includes comprehensive error handling and alerting capabilities.

## Overview

This pipeline demonstrates a sophisticated multi-tenant data processing pattern where:
- **Multiple clients** share a single Kafka topic
- Each client gets **dedicated schemas** and tables
- Data flows through **medallion architecture** (Bronze → Silver → Gold)
- Errors are **handled gracefully** without stopping the entire pipeline
- **Automated alerting** notifies on failures
- Runs on **serverless compute** for optimal cost and performance

## Architecture

### Data Flow

```
Kafka Stream (multi-client)
    ↓
kafka_raw_bronze (all clients combined)
    ↓
[Per-Client Bronze Tables]
    ├── bronze_client_001
    ├── bronze_client_002
    └── bronze_client_00X
    ↓
[Per-Client Silver Tables]
    ├── silver_client_001 (cleaned & enriched)
    ├── silver_client_002
    └── silver_client_00X
    ↓
[Per-Client Gold Tables]
    ├── gold_client_001_summary (aggregated metrics)
    ├── gold_client_002_summary
    └── gold_client_00X_summary
```

### Key Features

1. **Multi-Client Support**: Automatically routes data to client-specific tables
2. **Error Resilience**: Uses `expect_or_drop` and try-catch patterns to continue on failures
3. **Centralized Error Tracking**: All errors logged to `pipeline_errors` table
4. **Health Monitoring**: Real-time pipeline health view per client
5. **Email Alerts**: Configured notifications on pipeline failures
6. **Serverless Compute**: Auto-scaling, cost-efficient infrastructure

## Expected Kafka Message Format

The pipeline expects JSON messages with the following structure:

```json
{
  "client_id": "client_001",
  "client_name": "Example Corp",
  "timestamp": "2026-02-02T10:30:00Z",
  "event_type": "transaction",
  "data": {
    "key1": "value1",
    "key2": "value2"
  },
  "amount": 150.50,
  "status": "completed",
  "metadata": {
    "source": "web",
    "region": "us-east"
  }
}
```

**Required Fields:**
- `client_id` (string): Unique identifier for the client
- `timestamp` (ISO 8601 timestamp): Event timestamp

**Optional Fields:**
- `client_name`, `event_type`, `data`, `amount`, `status`, `metadata`

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- Kafka cluster accessible from Databricks
- Databricks CLI installed locally
- Appropriate permissions to create pipelines and tables

## Setup Instructions

### 1. Configure Variables

Edit `databricks.yml` and set the following variables:

```yaml
variables:
  kafka_bootstrap_servers: "your-kafka-server:9092"
  kafka_topic: "your-topic-name"
  kafka_consumer_group: "dlt_kafka_consumer"
  alert_email: "your-email@example.com"
  catalog: "your_catalog"
  schema: "kafka_pipeline"
```

### 2. Configure Clients

Edit `src/kafka_dlt_pipeline.ipynb` and update the `KNOWN_CLIENTS` list with your client IDs:

```python
KNOWN_CLIENTS = [
    "client_001",
    "client_002",
    "client_003"
]
```

**Note:** For production, consider dynamically discovering clients or reading from a configuration table.

### 3. Deploy the Bundle

```bash
# Validate the bundle
databricks bundle validate -t dev

# Deploy to development
databricks bundle deploy -t dev

# Start the pipeline
databricks bundle run kafka_client_pipeline -t dev
```

### 4. Monitor the Pipeline

```sql
-- View pipeline errors
SELECT * FROM your_catalog.kafka_pipeline_dev.pipeline_errors
ORDER BY error_timestamp DESC;

-- Check pipeline health
SELECT * FROM your_catalog.kafka_pipeline_dev.pipeline_health_monitor;

-- Monitor client activity
SELECT client_id, COUNT(*) as record_count
FROM your_catalog.kafka_pipeline_dev.kafka_raw_bronze
GROUP BY client_id;
```

## Error Handling Strategy

### 1. Expect or Drop
Tables use DLT expectations with `expect_or_drop` to handle malformed data:

```python
@dlt.expect_or_drop("valid_client_id", f"client_id = '{client_id}'")
@dlt.expect_or_drop("not_null_timestamp", "event_timestamp IS NOT NULL")
```

### 2. Try-Catch Blocks
Each table creation is wrapped in try-catch to prevent cascading failures:

```python
try:
    return dlt.read_stream(...)
except Exception as e:
    logger.error(f"Error: {str(e)}")
    send_alert(client_id, table_name, str(e))
    return spark.createDataFrame([], schema="client_id STRING")
```

### 3. Centralized Error Tracking
All errors are logged to the `pipeline_errors` table for monitoring and debugging.

### 4. Email Notifications
Pipeline failures trigger automatic email alerts configured in `resources/pipeline.yml`.

## Table Descriptions

### Common Tables

| Table Name | Type | Description |
|------------|------|-------------|
| `kafka_raw_bronze` | Streaming Table | Raw Kafka messages from all clients |
| `client_list` | Table | Unique list of all clients seen |
| `pipeline_errors` | Table | Centralized error log |
| `pipeline_health_monitor` | View | Real-time health metrics |

### Per-Client Tables

For each client (e.g., `client_001`):

| Table Name | Type | Description |
|------------|------|-------------|
| `bronze_client_001` | Streaming Table | Raw validated data for the client |
| `silver_client_001` | Streaming Table | Cleaned and enriched data |
| `gold_client_001_summary` | Streaming Table | Hourly aggregated metrics |

## Data Quality Rules

### Bronze Layer
- Valid client_id
- Non-null event timestamp

### Silver Layer
- Status must be in: `active`, `pending`, `completed`, `failed`
- Amount must be >= 0
- Event type must not be null

### Gold Layer
- Aggregates data into 1-hour windows
- Provides metrics: count, sum, avg, min, max

## Configuration Options

### Pipeline Settings (`resources/pipeline.yml`)

- **serverless**: Set to `true` for serverless compute
- **continuous**: Set to `true` for continuous processing
- **channel**: Set to `PREVIEW` for latest features

### Kafka Settings

Configure in pipeline configuration section:
- `kafka.bootstrap.servers`: Kafka server addresses
- `kafka.topic`: Topic to subscribe to
- `kafka.consumer.group.id`: Consumer group identifier

## Deployment Targets

### Development (`dev`)
- Mode: `development`
- Schema: `kafka_pipeline_dev`
- For testing and iteration

### Production (`prod`)
- Mode: `production`
- Schema: `kafka_pipeline_prod`
- For live data processing

## Monitoring and Troubleshooting

### Check Pipeline Status

```bash
# View pipeline runs
databricks pipelines list-updates --pipeline-id <pipeline-id>

# Get pipeline details
databricks pipelines get --pipeline-id <pipeline-id>
```

### Query Error Table

```sql
-- Recent errors by client
SELECT 
    client_id,
    table_name,
    COUNT(*) as error_count,
    MAX(error_timestamp) as last_error
FROM your_catalog.kafka_pipeline_dev.pipeline_errors
WHERE error_timestamp >= current_timestamp() - INTERVAL 1 DAY
GROUP BY client_id, table_name
ORDER BY error_count DESC;
```

### Common Issues

1. **Kafka Connection Errors**
   - Verify `kafka.bootstrap.servers` is correct
   - Check network connectivity from Databricks
   - Ensure Kafka topic exists

2. **Schema Errors**
   - Verify Unity Catalog permissions
   - Check that catalog and schema exist
   - Ensure proper naming conventions

3. **Data Quality Failures**
   - Check the `pipeline_errors` table
   - Review DLT expectations in the notebook
   - Validate Kafka message format

## Extending the Pipeline

### Adding New Clients

1. Add client_id to `KNOWN_CLIENTS` list
2. Redeploy the bundle
3. Tables will be automatically created

### Modifying Message Schema

1. Update `message_schema` in the notebook
2. Adjust column selections in bronze/silver/gold functions
3. Test with sample data first

### Adding Custom Alerting

Modify the `send_alert()` function to integrate with:
- PagerDuty
- Slack
- Microsoft Teams
- Custom webhook endpoints

## Performance Optimization

- **Serverless compute** automatically scales based on workload
- **Auto-optimize** enabled on bronze tables
- **Deduplication** on Kafka offset and partition
- **Windowed aggregations** for efficient gold layer processing

## Security Considerations

- Use **secrets** for Kafka credentials:
  ```yaml
  kafka.sasl.jaas.config: "{{secrets/kafka/jaas_config}}"
  ```
- Implement **Unity Catalog permissions** per client
- Use **network isolation** for Kafka connectivity
- Enable **audit logging** for compliance

## Cost Management

- Serverless compute charges only for processing time
- Set up **budget alerts** in Databricks
- Monitor **pipeline efficiency** metrics
- Consider **batch processing** for non-real-time clients

## Support and Documentation

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Delta Live Tables Documentation](https://docs.databricks.com/delta-live-tables/index.html)
- [Structured Streaming + Kafka Guide](https://docs.databricks.com/structured-streaming/kafka.html)

## License

This project is provided as-is for educational and production use.

## Author

Created as part of Databricks Asset Bundles best practices demonstration.

