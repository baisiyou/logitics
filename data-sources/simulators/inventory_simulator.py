#!/usr/bin/env python3
"""
Inventory Update Data Simulator
Simulates warehouse inventory changes and sends to Kafka inventory_updates topic
"""

import json
import time
import random
from confluent_kafka import Producer
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = 'inventory_updates'

WAREHOUSES = [
    {'id': 'WH001', 'name': 'Montreal Warehouse', 'lat': 45.5017, 'lon': -73.5673},
    {'id': 'WH002', 'name': 'Montreal Warehouse East', 'lat': 45.5017, 'lon': -73.5673},
    {'id': 'WH003', 'name': 'Montreal Warehouse West', 'lat': 45.5017, 'lon': -73.5673},
    {'id': 'WH004', 'name': 'Montreal Warehouse North', 'lat': 45.5017, 'lon': -73.5673},
]

PRODUCTS = [f'P{i:03d}' for i in range(1, 101)]  # 100 products
UPDATE_TYPES = ['INBOUND', 'OUTBOUND', 'TRANSFER', 'ADJUSTMENT']


def generate_inventory_update():
    """Generate inventory update"""
    warehouse = random.choice(WAREHOUSES)
    product = random.choice(PRODUCTS)
    update_type = random.choice(UPDATE_TYPES)
    
    # Set quantity change based on update type
    if update_type == 'INBOUND':
        quantity_change = random.randint(10, 100)
    elif update_type == 'OUTBOUND':
        quantity_change = -random.randint(5, 50)
    elif update_type == 'TRANSFER':
        quantity_change = -random.randint(10, 30)  # Negative for outgoing
    else:  # ADJUSTMENT
        quantity_change = random.randint(-10, 10)
    
    # Simulate current stock (simplified)
    current_stock = random.randint(0, 1000)
    
    update = {
        'warehouse_id': warehouse['id'],
        'warehouse_name': warehouse['name'],
        'product_id': product,
        'timestamp': int(time.time() * 1000),
        'update_type': update_type,
        'quantity_change': quantity_change,
        'current_stock': current_stock,
        'reserved_stock': random.randint(0, current_stock // 2),
        'available_stock': current_stock - random.randint(0, current_stock // 2)
    }
    
    return update


def delivery_report(err, msg):
    """Kafka message delivery callback"""
    if err is not None:
        print(f'Message delivery failed: {err}')


def main():
    """Main function"""
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'inventory-simulator'
    })
    
    print(f"Starting to send inventory update data to topic: {TOPIC}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            update = generate_inventory_update()
            
            producer.produce(
                TOPIC,
                key=f"{update['warehouse_id']}_{update['product_id']}",
                value=json.dumps(update),
                callback=delivery_report
            )
            
            producer.poll(0)
            time.sleep(random.uniform(0.5, 2.0))  # Update every 0.5-2 seconds
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.flush()
        print("Stopped sending")


if __name__ == '__main__':
    main()

