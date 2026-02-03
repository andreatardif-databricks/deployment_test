# 🚀 Quick Start - Get Running in 10 Minutes

This guide will get your Kafka Alerting Pipeline running from scratch in about 10 minutes.

## Prerequisites

- Docker Desktop installed and running
- Databricks CLI configured (`databricks configure --token`)
- Git (optional)

## Step 1: Start Kafka Locally (2 minutes)

```bash
cd kafka_alerting_pipeline

# Option A: Use the setup script (recommended)
./setup-kafka.sh

# Option B: Manual setup
docker compose up -d
sleep 30
docker exec kafka-broker kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

**Verify Kafka is running:**
- Kafka UI: http://localhost:8080
- Bootstrap Server: `localhost:9092`
- Topic: `client-events`

## Step 2: Configure the Pipeline (1 minute)

Edit `databricks.yml` (lines 14-20):

```yaml
variables:
  kafka_bootstrap_servers: "localhost:9092"      # ← Change this
  kafka_topic: "client-events"                   # ← Change this
  kafka_consumer_group: "dlt_kafka_consumer"
  alert_email: "your-email@example.com"          # ← Change this
  catalog: "andrea_tardif"                       # ← Your catalog
  schema: "kafka_pipeline"
```

## Step 3: Configure Clients (1 minute)

Edit `src/kafka_dlt_pipeline.ipynb`, cell 16, update the `KNOWN_CLIENTS` list:

```python
KNOWN_CLIENTS = [
    "client_001",
    "client_002",
    "client_003"
]
```

## Step 4: Validate & Deploy (2 minutes)

```bash
# Validate configuration
databricks bundle validate -t dev

# Deploy to Databricks
databricks bundle deploy -t dev
```

## Step 5: Send Test Data (2 minutes)

**Option A: Using the data generator notebook**

1. Open Databricks workspace
2. Navigate to: `/Workspace/Users/your-email@databricks.com/.bundle/kafka_alerting_pipeline/dev/files/src/kafka_data_generator.ipynb`
3. Update cell 2:
   ```python
   KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
   KAFKA_TOPIC = "client-events"
   ```
4. Run all cells
5. Uncomment the Kafka write lines and run again

**Option B: Using command line**

```bash
# Send a test message
docker exec -i kafka-broker kafka-console-producer \
  --topic client-events \
  --bootstrap-server localhost:9092 << EOF
{"client_id":"client_001","client_name":"Acme Corp","timestamp":"2026-02-02T10:00:00Z","event_type":"transaction","amount":150.50,"status":"completed","data":{"key":"value"},"metadata":{"source":"test"}}
EOF

# Verify message was sent
docker exec kafka-broker kafka-console-consumer \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --max-messages 1
```

## Step 6: Start the Pipeline (2 minutes)

**Option A: Via CLI**
```bash
databricks bundle run kafka_client_pipeline -t dev
```

**Option B: Via Databricks UI**
1. Go to Databricks workspace
2. Navigate to: **Workflows** → **Delta Live Tables**
3. Find: `kafka_client_pipeline_dev`
4. Click **Start**

## Step 7: Verify It's Working (2 minutes)

### Check Pipeline Status

In Databricks UI:
1. Go to **Delta Live Tables**
2. Click on `kafka_client_pipeline_dev`
3. You should see:
   - Green checkmarks on tables
   - Data flowing through the lineage
   - No errors

### Query the Tables

In a Databricks SQL notebook:

```sql
-- Set catalog
USE CATALOG andrea_tardif;
USE SCHEMA kafka_pipeline_dev;

-- Check raw data
SELECT * FROM kafka_raw_bronze LIMIT 10;

-- Check client-specific data
SELECT * FROM bronze_client_001 LIMIT 10;
SELECT * FROM silver_client_001 LIMIT 10;
SELECT * FROM gold_client_001_summary LIMIT 10;

-- Check for errors
SELECT * FROM pipeline_errors ORDER BY error_timestamp DESC;

-- View all clients
SELECT * FROM client_list;
```

## 🎉 Success Criteria

You're all set when you see:

- ✅ Kafka running (check http://localhost:8080)
- ✅ Pipeline status: "Running" in Databricks
- ✅ Data in `kafka_raw_bronze` table
- ✅ Data in client-specific bronze tables
- ✅ Data in silver tables (cleaned)
- ✅ Data in gold tables (aggregated)
- ✅ No critical errors in `pipeline_errors`

## Troubleshooting

### Kafka won't start
```bash
# Check Docker
docker ps

# View logs
docker compose logs -f kafka

# Restart
docker compose down
docker compose up -d
```

### Pipeline can't connect to Kafka from Databricks
**Problem:** Databricks cloud can't reach `localhost:9092`

**Solution:** Use one of these:

1. **Confluent Cloud (Recommended)**
   - Sign up at https://confluent.cloud
   - Create free cluster
   - Get bootstrap server (e.g., `pkc-xxx.us-east-1.aws.confluent.cloud:9092`)
   - Update `databricks.yml`

2. **ngrok tunnel (Dev only)**
   ```bash
   # Install ngrok
   brew install ngrok

   # Create tunnel
   ngrok tcp 9092

   # Use ngrok URL as bootstrap server
   ```

### No data in tables
```bash
# Check if topic has data
docker exec kafka-broker kafka-console-consumer \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --max-messages 5

# Check pipeline expectations
# Look at pipeline_errors table in Databricks
```

### "Topic does not exist"
```bash
# Create topic
docker exec kafka-broker kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

## Continuous Data Generation

To continuously send data for testing:

```python
# In the kafka_data_generator.ipynb notebook
# Uncomment the streaming section (cell 7)
# This will generate 10 messages per second

query = rate_stream.writeStream \
    .foreachBatch(generate_streaming_data) \
    .outputMode("update") \
    .start()

query.awaitTermination()
```

## Stop Everything

```bash
# Stop pipeline (in Databricks UI)
# Go to DLT pipeline → Stop

# Stop Kafka
docker compose down

# Or keep data for next time
docker compose stop
```

## Next Steps

1. **Customize the schema:** Edit `message_schema` in the main notebook
2. **Add more clients:** Update `KNOWN_CLIENTS` list
3. **Modify transformations:** Edit silver/gold table logic
4. **Set up monitoring:** Use `pipeline_monitoring.ipynb`
5. **Deploy to production:** `databricks bundle deploy -t prod`

## Useful Commands

```bash
# View Kafka logs
docker compose logs -f kafka

# List topics
docker exec kafka-broker kafka-topics --list \
  --bootstrap-server localhost:9092

# Consumer group status
docker exec kafka-broker kafka-consumer-groups --describe \
  --group dlt_kafka_consumer \
  --bootstrap-server localhost:9092

# Pipeline status
databricks pipelines get --pipeline-id <id>

# View pipeline updates
databricks pipelines list-updates --pipeline-id <id>
```

## Resources

- **Full Documentation:** See `README.md`
- **Kafka Setup:** See `KAFKA_SETUP_GUIDE.md`
- **Detailed Setup:** See `SETUP_GUIDE.md`
- **Project Overview:** See `PROJECT_SUMMARY.md`

## Architecture Reminder

```
Kafka (localhost:9092) 
    ↓ [client-events topic]
DLT Pipeline (Databricks)
    ↓ kafka_raw_bronze
    ↓ bronze_client_XXX
    ↓ silver_client_XXX (cleaned)
    ↓ gold_client_XXX_summary (1hr windows)
```

---

**Estimated Total Time:** 10-15 minutes
**Difficulty:** Beginner-friendly

Happy streaming! 🎊

