# Quick Setup Guide - Kafka Alerting Pipeline

This guide will help you get the Kafka Alerting Pipeline up and running in under 15 minutes.

## Prerequisites Checklist

- [ ] Databricks workspace with Unity Catalog enabled
- [ ] Databricks CLI installed (`pip install databricks-cli`)
- [ ] Access to a Kafka cluster
- [ ] Unity Catalog permissions (CREATE TABLE, CREATE SCHEMA)
- [ ] Email address for alerts

## Step-by-Step Setup

### 1. Configure Databricks CLI

```bash
# Configure authentication
databricks configure --token

# Enter your workspace URL when prompted
# Example: https://your-workspace.cloud.databricks.com

# Enter your personal access token
```

### 2. Update Configuration

Edit `databricks.yml` and update these variables:

```yaml
variables:
  kafka_bootstrap_servers: "your-kafka-server:9092"  # Your Kafka server
  kafka_topic: "your-topic-name"                      # Your Kafka topic
  alert_email: "your-email@example.com"               # Alert recipient
  catalog: "your_catalog"                             # Your Unity Catalog
  schema: "kafka_pipeline"                            # Schema name
```

### 3. Update Client List

Edit `src/kafka_dlt_pipeline.ipynb`, find the `KNOWN_CLIENTS` list (around cell 16):

```python
KNOWN_CLIENTS = [
    "client_001",  # Replace with your actual client IDs
    "client_002",
    "client_003",
]
```

**Important:** These client IDs must match the `client_id` field in your Kafka messages.

### 4. (Optional) Test Kafka Connection

Before deploying, verify Kafka connectivity:

```python
# Run this in a Databricks notebook
from pyspark.sql.functions import *

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "your-kafka-server:9092") \
    .option("subscribe", "your-topic") \
    .option("startingOffsets", "earliest") \
    .load()

df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)").display()
```

### 5. Validate Bundle Configuration

```bash
cd kafka_alerting_pipeline
databricks bundle validate -t dev
```

Expected output:
```
✓ Configuration is valid
```

### 6. Deploy to Development

```bash
databricks bundle deploy -t dev
```

This will:
- Upload your notebooks to Databricks
- Create the DLT pipeline
- Configure notifications
- Set up serverless compute

### 7. Start the Pipeline

**Option A: Via CLI**
```bash
databricks bundle run kafka_client_pipeline -t dev
```

**Option B: Via Databricks UI**
1. Navigate to **Workflows** → **Delta Live Tables**
2. Find **kafka_client_pipeline_dev**
3. Click **Start**

### 8. Monitor Pipeline Execution

**Watch the pipeline:**
```bash
# Get pipeline ID from deployment output
databricks pipelines get --pipeline-id <pipeline-id>

# View update history
databricks pipelines list-updates --pipeline-id <pipeline-id>
```

**In the UI:**
1. Go to **Delta Live Tables**
2. Click on your pipeline
3. View the lineage graph
4. Monitor each table's status

### 9. Verify Data Flow

```sql
-- Check if data is arriving
SELECT * FROM your_catalog.kafka_pipeline_dev.kafka_raw_bronze LIMIT 10;

-- Check client distribution
SELECT client_id, COUNT(*) as record_count
FROM your_catalog.kafka_pipeline_dev.kafka_raw_bronze
GROUP BY client_id;

-- View client-specific bronze data
SELECT * FROM your_catalog.kafka_pipeline_dev.bronze_client_001 LIMIT 10;

-- Check silver layer
SELECT * FROM your_catalog.kafka_pipeline_dev.silver_client_001 LIMIT 10;

-- View aggregated gold metrics
SELECT * FROM your_catalog.kafka_pipeline_dev.gold_client_001_summary LIMIT 10;
```

### 10. Check Error Handling

```sql
-- View any errors
SELECT * FROM your_catalog.kafka_pipeline_dev.pipeline_errors
ORDER BY error_timestamp DESC;

-- Check pipeline health
SELECT * FROM your_catalog.kafka_pipeline_dev.pipeline_health_monitor;
```

## Sending Test Data

Use the provided data generator notebook:

1. Open `src/kafka_data_generator.ipynb` in Databricks
2. Update Kafka configuration in cell 2
3. Run all cells to generate sample data
4. Uncomment the write commands to send data to Kafka

## Common Issues and Solutions

### Issue: "Kafka broker not reachable"

**Solution:**
- Verify Kafka server address and port
- Check network connectivity from Databricks
- Ensure Kafka topic exists
- Verify security settings (if using authenticated Kafka)

### Issue: "Permission denied creating table"

**Solution:**
```sql
-- Grant necessary permissions
GRANT CREATE TABLE ON CATALOG your_catalog TO `your-email@example.com`;
GRANT USE CATALOG ON CATALOG your_catalog TO `your-email@example.com`;
GRANT USE SCHEMA ON SCHEMA your_catalog.kafka_pipeline_dev TO `your-email@example.com`;
```

### Issue: "No data in bronze tables"

**Solution:**
1. Check if Kafka is sending data
2. Verify topic name matches configuration
3. Check pipeline expectations (might be dropping all data)
4. Look at `pipeline_errors` table for clues

### Issue: "Pipeline stuck in 'Starting' state"

**Solution:**
- Check serverless compute availability in your region
- Verify workspace has serverless enabled
- Check for quota limits

## Production Deployment

Once tested in dev, deploy to production:

```bash
# Update production variables in databricks.yml
# Then deploy
databricks bundle deploy -t prod

# Start production pipeline
databricks bundle run kafka_client_pipeline -t prod
```

**Production Checklist:**
- [ ] Update Kafka credentials to use secrets
- [ ] Configure proper Unity Catalog permissions
- [ ] Set up monitoring dashboards
- [ ] Configure alerting (already in bundle)
- [ ] Document client onboarding process
- [ ] Set up backup and disaster recovery
- [ ] Review cost optimization settings

## Next Steps

1. **Add More Clients:** Update `KNOWN_CLIENTS` list and redeploy
2. **Customize Transformations:** Modify silver/gold table logic
3. **Add Custom Alerts:** Integrate with Slack/PagerDuty
4. **Create Dashboards:** Build Databricks SQL dashboards
5. **Auto-Discovery:** Implement dynamic client discovery

## Getting Help

- **DLT Documentation:** https://docs.databricks.com/delta-live-tables/
- **Kafka Integration:** https://docs.databricks.com/structured-streaming/kafka.html
- **Databricks Asset Bundles:** https://docs.databricks.com/dev-tools/bundles/

## Architecture Diagram

```
┌─────────────────┐
│  Kafka Stream   │
│  (All Clients)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  kafka_raw_bronze       │ ◄─── Raw ingestion
│  (All clients combined) │
└────────┬────────────────┘
         │
         ├──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │bronze_ │ │bronze_ │ │bronze_ │ │bronze_ │
    │client_1│ │client_2│ │client_3│ │client_N│
    └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │silver_ │ │silver_ │ │silver_ │ │silver_ │
    │client_1│ │client_2│ │client_3│ │client_N│
    └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │ gold_  │ │ gold_  │ │ gold_  │ │ gold_  │
    │client_1│ │client_2│ │client_3│ │client_N│
    └────────┘ └────────┘ └────────┘ └────────┘

         All errors flow to
               ▼
    ┌──────────────────────┐
    │  pipeline_errors     │ ◄─── Centralized error log
    └──────────────────────┘
```

## Success Criteria

Your pipeline is working correctly when:
- ✅ Pipeline status shows "Running"
- ✅ Data appears in `kafka_raw_bronze` table
- ✅ Client-specific bronze tables have data
- ✅ Silver tables show enriched data
- ✅ Gold tables show hourly aggregations
- ✅ No critical errors in `pipeline_errors` table
- ✅ Email alerts configured and tested

Congratulations! Your Kafka Alerting Pipeline is now operational. 🎉

