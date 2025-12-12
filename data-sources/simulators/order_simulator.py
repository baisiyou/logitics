#!/usr/bin/env python3
"""
Order Data Simulator
Simulates real-time order stream and sends to Kafka orders topic
"""

import json
import time
import random
from datetime import datetime, timedelta
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')
SCHEMA_REGISTRY_URL = os.getenv('CONFLUENT_SCHEMA_REGISTRY_URL', 'http://localhost:8081')
TOPIC = 'orders'

# Simulated data configuration
CITIES = ['Montreal', 'Toronto', 'Vancouver', 'Calgary', 'Ottawa', 'Edmonton', 'Winnipeg', 'Quebec City']
PRIORITIES = ['STANDARD', 'EXPRESS', 'SAME_DAY']
PRODUCTS = [
    {'id': 'P001', 'weight': 0.5, 'dimensions': [20, 15, 10]},
    {'id': 'P002', 'weight': 1.2, 'dimensions': [30, 25, 20]},
    {'id': 'P003', 'weight': 2.5, 'dimensions': [40, 30, 25]},
    {'id': 'P004', 'weight': 0.3, 'dimensions': [15, 10, 5]},
    {'id': 'P005', 'weight': 5.0, 'dimensions': [50, 40, 30]},
]

# City coordinates (simplified)
CITY_COORDS = {
    'Montreal': {'lat': 45.5017, 'lon': -73.5673},
    'Toronto': {'lat': 43.6532, 'lon': -79.3832},
    'Vancouver': {'lat': 49.2827, 'lon': -123.1207},
    'Calgary': {'lat': 51.0447, 'lon': -114.0719},
    'Ottawa': {'lat': 45.4215, 'lon': -75.6972},
    'Edmonton': {'lat': 53.5461, 'lon': -113.4938},
    'Winnipeg': {'lat': 49.8951, 'lon': -97.1384},
    'Quebec City': {'lat': 46.8139, 'lon': -71.2080},
}


def generate_order():
    """Generate simulated order"""
    order_id = f"ORD{int(time.time() * 1000)}{random.randint(1000, 9999)}"
    customer_id = f"CUST{random.randint(10000, 99999)}"
    city = random.choice(CITIES)
    coords = CITY_COORDS[city]
    
    # Add random offset to simulate different areas within the city
    lat = coords['lat'] + random.uniform(-0.1, 0.1)
    lon = coords['lon'] + random.uniform(-0.1, 0.1)
    
    # Generate order items
    num_items = random.randint(1, 5)
    items = []
    for _ in range(num_items):
        product = random.choice(PRODUCTS)
        items.append({
            'product_id': product['id'],
            'quantity': random.randint(1, 3),
            'weight_kg': product['weight'],
            'dimensions': {
                'length_cm': product['dimensions'][0],
                'width_cm': product['dimensions'][1],
                'height_cm': product['dimensions'][2]
            }
        })
    
    priority = random.choices(
        PRIORITIES,
        weights=[0.7, 0.25, 0.05]  # 70% standard, 25% express, 5% same day
    )[0]
    
    timestamp = int(time.time() * 1000)
    
    # Expected delivery time (same day: within 2 hours; express: within 4 hours; standard: within 24 hours)
    if priority == 'SAME_DAY':
        preferred_time = timestamp + random.randint(3600000, 7200000)  # 1-2 hours
    elif priority == 'EXPRESS':
        preferred_time = timestamp + random.randint(7200000, 14400000)  # 2-4 hours
    else:
        preferred_time = timestamp + random.randint(14400000, 86400000)  # 4-24 hours
    
    order = {
        'order_id': order_id,
        'customer_id': customer_id,
        'timestamp': timestamp,
        'delivery_address': {
            'street': f"{random.randint(1, 999)} Main Street",
            'city': city,
            'state': 'Canada',
            'zip_code': f"{random.choice(['H', 'K', 'M', 'T', 'V'])}{random.randint(1, 9)}{random.choice(['A', 'B', 'C', 'E', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'V', 'X', 'Y', 'Z'])}{random.randint(0, 9)}{random.choice(['A', 'B', 'C', 'E', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z'])}{random.randint(0, 9)}",
            'latitude': lat,
            'longitude': lon
        },
        'items': items,
        'priority': priority,
        'preferred_delivery_time': preferred_time
    }
    
    return order


def delivery_report(err, msg):
    """Kafka message delivery callback"""
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message sent to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}')


def main():
    """Main function"""
    # Create Kafka producer
    producer_config = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'order-simulator'
    }
    
    producer = Producer(producer_config)
    
    print(f"Starting to send order data to topic: {TOPIC}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            order = generate_order()
            
            # Send message (using JSON serialization, should use Avro in production)
            producer.produce(
                TOPIC,
                key=order['order_id'],
                value=json.dumps(order),
                callback=delivery_report
            )
            
            producer.poll(0)
            
            # Control sending frequency: average 2-5 orders per second
            time.sleep(random.uniform(0.2, 0.5))
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.flush()
        print("Stopped sending")


if __name__ == '__main__':
    main()

