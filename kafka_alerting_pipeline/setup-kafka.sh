#!/bin/bash

# Setup script for local Kafka development environment
# This script starts Kafka and creates the required topic

set -e

echo "🚀 Setting up Kafka for Kafka Alerting Pipeline..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"

# Start Kafka using docker compose
echo ""
echo "📦 Starting Kafka and Zookeeper..."
docker compose up -d

# Wait for Kafka to be ready
echo ""
echo "⏳ Waiting for Kafka to be ready (30 seconds)..."
sleep 30

# Check if Kafka is running
if docker ps | grep -q kafka-broker; then
    echo "✓ Kafka broker is running"
else
    echo "❌ Error: Kafka broker failed to start"
    docker compose logs kafka
    exit 1
fi

# Create the topic
echo ""
echo "📝 Creating Kafka topic 'client-events'..."
docker exec kafka-broker kafka-topics --create \
  --topic client-events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

# List topics to verify
echo ""
echo "📋 Available topics:"
docker exec kafka-broker kafka-topics --list \
  --bootstrap-server localhost:9092

# Describe the topic
echo ""
echo "ℹ️  Topic details:"
docker exec kafka-broker kafka-topics --describe \
  --topic client-events \
  --bootstrap-server localhost:9092

echo ""
echo "✅ Kafka setup complete!"
echo ""
echo "📊 Kafka UI available at: http://localhost:8080"
echo "🔌 Bootstrap Server: localhost:9092"
echo "📢 Topic: client-events"
echo ""
echo "Next steps:"
echo "1. Update databricks.yml with:"
echo "   kafka_bootstrap_servers: localhost:9092"
echo "   kafka_topic: client-events"
echo ""
echo "2. Use src/kafka_data_generator.ipynb to send test data"
echo ""
echo "3. Deploy the DLT pipeline:"
echo "   databricks bundle deploy -t dev"
echo ""
echo "To stop Kafka:"
echo "   docker compose down"
echo ""
echo "To view Kafka logs:"
echo "   docker compose logs -f kafka"

