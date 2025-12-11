#!/usr/bin/env python3
"""
Send test alerts directly to Kafka for testing
"""

import json
import time
from confluent_kafka import Producer
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')

producer = Producer({
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'client.id': 'test-alert-sender'
})

# Test anomaly alert
anomaly_alert = {
    'entity_type': 'order',
    'entity_id': 'ORD_TEST_001',
    'is_anomaly': True,
    'anomaly_score': 0.85,
    'anomaly_type': 'LARGE_ORDER',
    'severity': 'MEDIUM',
    'description': 'Order item count anomaly: 25 items',
    'timestamp': int(time.time() * 1000)
}

# Test warehouse pressure alert
pressure_alert = {
    'warehouse_id': 'WH001',
    'pressure_level': 'HIGH',
    'pressure_score': 0.75,
    'current_utilization': 0.85,
    'pending_orders': 150,
    'estimated_completion_time_minutes': 120,
    'recommendations': [
        'Increase sorting staff',
        'Extend working hours',
        'Optimize sorting process'
    ],
    'severity': 'HIGH',
    'timestamp': int(time.time() * 1000)
}

print("Sending test alerts to Kafka...")

# Send anomaly alert
producer.produce(
    'anomaly_alerts',
    key='TEST_ORDER_001'.encode('utf-8'),
    value=json.dumps(anomaly_alert).encode('utf-8')
)
print("✅ Sent anomaly alert")

# Send warehouse pressure alert
producer.produce(
    'warehouse_pressure_alerts',
    key='WH001'.encode('utf-8'),
    value=json.dumps(pressure_alert).encode('utf-8')
)
print("✅ Sent warehouse pressure alert")

producer.flush()
print("\n✅ Test alerts sent successfully!")
print("\nCheck alerts in dashboard or API:")
print("  curl http://localhost:8001/api/v1/alerts?limit=5")

