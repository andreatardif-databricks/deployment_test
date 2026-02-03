#!/usr/bin/env python3
"""
Send test data to Kafka for the Kafka Alerting Pipeline
"""
import json
import random
from datetime import datetime, timedelta
import subprocess
import sys

# Configuration
CLIENTS = [
    {"id": "client_001", "name": "Acme Corp"},
    {"id": "client_002", "name": "Global Industries"},
    {"id": "client_003", "name": "Tech Solutions"},
    {"id": "client_004", "name": "Finance Group"},
    {"id": "client_005", "name": "Retail Chain"}
]

EVENT_TYPES = ["transaction", "login", "purchase", "update", "delete"]
STATUSES = ["active", "pending", "completed", "failed"]

def generate_message():
    """Generate a single test message matching the expected schema."""
    client = random.choice(CLIENTS)
    return {
        "client_id": client["id"],
        "client_name": client["name"],
        "timestamp": (datetime.now() - timedelta(seconds=random.randint(0, 3600))).isoformat(),
        "event_type": random.choice(EVENT_TYPES),
        "data": {
            "key1": f"value_{random.randint(1, 100)}",
            "key2": f"data_{random.randint(1, 100)}",
            "source": random.choice(["web", "mobile", "api"])
        },
        "amount": round(random.uniform(10, 5000), 2),
        "status": random.choice(STATUSES),
        "metadata": {
            "source": random.choice(["web", "mobile", "api"]),
            "region": random.choice(["us-east", "us-west", "eu-west", "ap-south"]),
            "version": "1.0"
        }
    }

def send_to_kafka(num_messages=100):
    """Send messages to Kafka."""
    print(f"Generating {num_messages} test messages...")
    messages = [generate_message() for _ in range(num_messages)]
    
    # Count messages per client
    client_counts = {}
    for msg in messages:
        client_id = msg["client_id"]
        client_counts[client_id] = client_counts.get(client_id, 0) + 1
    
    print(f"\nMessage distribution:")
    for client_id, count in sorted(client_counts.items()):
        print(f"  {client_id}: {count} messages")
    
    print(f"\nSending to Kafka topic 'client-events'...")
    
    # Send to Kafka
    try:
        process = subprocess.Popen(
            ["docker", "exec", "-i", "kafka-broker", "kafka-console-producer",
             "--topic", "client-events",
             "--bootstrap-server", "localhost:9092"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        for msg in messages:
            process.stdin.write(json.dumps(msg) + "\n")
            process.stdin.flush()
        
        process.stdin.close()
        stdout, stderr = process.communicate(timeout=10)
        
        if process.returncode == 0:
            print(f"✅ Successfully sent {num_messages} messages to Kafka!")
            print("\nVerify with:")
            print("  docker exec kafka-broker kafka-console-consumer \\")
            print("    --topic client-events \\")
            print("    --bootstrap-server localhost:9092 \\")
            print("    --from-beginning \\")
            print("    --max-messages 5")
        else:
            print(f"❌ Error sending to Kafka:")
            print(stderr)
            sys.exit(1)
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ Timeout sending to Kafka")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Get number of messages from command line or use default
    num_messages = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    send_to_kafka(num_messages)

