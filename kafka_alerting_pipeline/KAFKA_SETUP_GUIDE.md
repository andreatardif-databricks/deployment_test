# Kafka Setup Guide

This guide covers setting up a Kafka bootstrap server and creating topics for the Kafka Alerting Pipeline.

## Overview

**Kafka Bootstrap Servers** are the initial contact points for Kafka clients. They provide the cluster metadata and help clients discover all Kafka brokers.

**Kafka Topics** are categories/feeds where messages are published.

## Option 1: Local Kafka Setup (Development/Testing)

### Using Docker Compose (Recommended for Local Dev)

Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    hostname: zookeeper
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    hostname: kafka
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9101:9101"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: localhost
```

**Start Kafka:**

```bash
# Start the containers
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f kafka
```

**Your Bootstrap Server:** `localhost:9092`

### Create a Topic

```bash
# Using Docker exec
docker exec -it kafka kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# List topics
docker exec -it kafka kafka-topics --list \
  --bootstrap-server localhost:9092

# Describe topic
docker exec -it kafka kafka-topics --describe \
  --topic client-events \
  --bootstrap-server localhost:9092
```

### Test the Topic

**Produce test messages:**

```bash
# Start a console producer
docker exec -it kafka kafka-console-producer \
  --topic client-events \
  --bootstrap-server localhost:9092

# Type messages (one per line):
{"client_id":"client_001","client_name":"Test","timestamp":"2026-02-02T10:00:00Z","event_type":"test","amount":100.0,"status":"active"}
```

**Consume messages:**

```bash
# Start a console consumer
docker exec -it kafka kafka-console-consumer \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --from-beginning
```

## Option 2: Using Homebrew (macOS)

```bash
# Install Kafka
brew install kafka

# Start Zookeeper
zookeeper-server-start /usr/local/etc/kafka/zookeeper.properties &

# Start Kafka
kafka-server-start /usr/local/etc/kafka/server.properties &

# Create topic
kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# List topics
kafka-topics --list --bootstrap-server localhost:9092
```

**Your Bootstrap Server:** `localhost:9092`

## Option 3: Cloud-Managed Kafka (Production)

### Confluent Cloud

1. **Sign up:** https://confluent.cloud
2. **Create a cluster:**
   - Go to Confluent Cloud Console
   - Click "Add cluster"
   - Choose Basic/Standard/Dedicated
   - Select region closest to Databricks

3. **Get Bootstrap Server:**
   - Go to Cluster Settings
   - Copy "Bootstrap server" (e.g., `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`)

4. **Create API Key:**
   - Go to "API Keys" in cluster
   - Create new key (save both Key and Secret)

5. **Create Topic:**
   - Go to "Topics" tab
   - Click "Create topic"
   - Name: `client-events`
   - Partitions: 3
   - Create

**Configuration for Databricks:**

```yaml
variables:
  kafka_bootstrap_servers: "pkc-xxxxx.us-east-1.aws.confluent.cloud:9092"
  kafka_topic: "client-events"
  kafka_sasl_mechanism: "PLAIN"
  kafka_security_protocol: "SASL_SSL"
```

Update `resources/pipeline.yml` to add security:

```yaml
configuration:
  kafka.bootstrap.servers: ${var.kafka_bootstrap_servers}
  kafka.topic: ${var.kafka_topic}
  kafka.security.protocol: SASL_SSL
  kafka.sasl.mechanism: PLAIN
  kafka.sasl.jaas.config: "org.apache.kafka.common.security.plain.PlainLoginModule required username='YOUR_API_KEY' password='YOUR_API_SECRET';"
```

### AWS MSK (Managed Streaming for Kafka)

1. **Create MSK Cluster:**
   ```bash
   aws kafka create-cluster \
     --cluster-name kafka-client-events \
     --kafka-version 3.5.1 \
     --number-of-broker-nodes 3 \
     --broker-node-group-info file://broker-info.json
   ```

2. **Get Bootstrap Servers:**
   ```bash
   aws kafka get-bootstrap-brokers --cluster-arn <cluster-arn>
   ```

3. **Create Topic:**
   ```bash
   kafka-topics --create \
     --topic client-events \
     --bootstrap-server <bootstrap-servers> \
     --partitions 3 \
     --replication-factor 3
   ```

### Azure Event Hubs (Kafka-Compatible)

1. **Create Event Hubs Namespace**
2. **Create Event Hub** (this is your topic)
3. **Get Connection String**

**Bootstrap Server:** `<namespace>.servicebus.windows.net:9093`

## Option 4: Databricks' Kafka for Testing

Databricks doesn't provide managed Kafka, but you can:

1. **Use Confluent Cloud** (recommended)
2. **Deploy Kafka on Databricks** (not recommended for production)
3. **Use Event Hubs** (Azure) or **MSK** (AWS)

## Connecting to Network-Accessible Kafka

If you have an existing Kafka cluster:

```bash
# Test connectivity from your machine
telnet <kafka-server> 9092

# Or using nc
nc -zv <kafka-server> 9092
```

**⚠️ Important:** Databricks must be able to reach your Kafka cluster:
- For cloud Kafka: Usually accessible via internet
- For private Kafka: Configure VPC peering or Private Link
- For localhost: Won't work from Databricks (use tunneling or cloud deployment)

## Recommended Setup for This Project

### For Development/Testing:

**Option A: Docker Compose (Local)**
```bash
# 1. Create docker-compose.yml (see above)
# 2. Start Kafka
docker-compose up -d

# 3. Create topic
docker exec -it kafka kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

**Option B: Confluent Cloud Free Tier**
- Free for development
- No infrastructure management
- Easy to connect from Databricks

### For Production:

**Recommended: Confluent Cloud or Cloud Provider Managed Service**
- Confluent Cloud (works anywhere)
- AWS MSK (if using AWS Databricks)
- Azure Event Hubs (if using Azure Databricks)

## Configure the Pipeline

Once you have Kafka running, update `databricks.yml`:

```yaml
variables:
  kafka_bootstrap_servers: "your-kafka-server:9092"  # Update this
  kafka_topic: "client-events"                        # Your topic name
  kafka_consumer_group: "dlt_kafka_consumer"
  alert_email: "your-email@example.com"
```

## Testing from Databricks

Create a test notebook in Databricks:

```python
# Test Kafka connectivity
from pyspark.sql.functions import *

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "your-kafka-server:9092") \
    .option("subscribe", "client-events") \
    .option("startingOffsets", "earliest") \
    .load()

# Display messages
display(
    df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
)
```

If this works, your Kafka setup is ready!

## Sending Test Data

Use the provided data generator notebook:

1. Open `src/kafka_data_generator.ipynb`
2. Update configuration:
   ```python
   KAFKA_BOOTSTRAP_SERVERS = "your-kafka-server:9092"
   KAFKA_TOPIC = "client-events"
   ```
3. Run cells to generate and send data

## Common Issues

### Issue: "Connection refused"
**Solution:** 
- Check Kafka is running: `docker ps` or `brew services list`
- Verify port 9092 is not blocked
- Check bootstrap server address

### Issue: "Topic does not exist"
**Solution:**
```bash
# Create the topic first
docker exec -it kafka kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

### Issue: Databricks can't connect to localhost:9092
**Solution:** localhost won't work from Databricks cloud. Options:
1. Use Confluent Cloud (recommended)
2. Expose Kafka via ngrok (development only)
3. Deploy Kafka in the cloud

### Issue: Authentication failed
**Solution:** 
- For Confluent Cloud: verify API key/secret
- For MSK: check IAM roles
- Update `kafka.sasl.jaas.config` with correct credentials

## Quick Start: Docker + Test Data

Complete setup in 5 minutes:

```bash
# 1. Create docker-compose.yml (from above)
# 2. Start Kafka
docker-compose up -d

# 3. Wait 30 seconds for startup
sleep 30

# 4. Create topic
docker exec -it kafka kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# 5. Send test message
echo '{"client_id":"client_001","client_name":"Test Corp","timestamp":"2026-02-02T10:00:00Z","event_type":"transaction","amount":150.50,"status":"completed","data":{"key":"value"},"metadata":{"source":"test"}}' | \
docker exec -i kafka kafka-console-producer \
  --topic client-events \
  --bootstrap-server localhost:9092

# 6. Verify message
docker exec -it kafka kafka-console-consumer \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --from-beginning \
  --max-messages 1
```

## Next Steps

1. ✅ Set up Kafka (local or cloud)
2. ✅ Create topic (`client-events`)
3. ✅ Test connectivity
4. ✅ Update `databricks.yml` with bootstrap server
5. ✅ Use `kafka_data_generator.ipynb` to send test data
6. ✅ Deploy and run the DLT pipeline

## Resources

- [Apache Kafka Quickstart](https://kafka.apache.org/quickstart)
- [Confluent Cloud](https://confluent.cloud)
- [AWS MSK](https://aws.amazon.com/msk/)
- [Azure Event Hubs](https://azure.microsoft.com/en-us/services/event-hubs/)
- [Databricks Kafka Integration](https://docs.databricks.com/structured-streaming/kafka.html)

---

**For this project, I recommend:**
- **Development:** Docker Compose (local) or Confluent Cloud (free tier)
- **Production:** Confluent Cloud or cloud provider managed service

Need help? Check the troubleshooting section or the Databricks Kafka documentation!

