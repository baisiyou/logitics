#!/usr/bin/env python3
"""
Vehicle Location Data Simulator
Simulates real-time vehicle GPS location stream and sends to Kafka vehicle_locations topic
"""

import json
import time
import random
from confluent_kafka import Producer
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = 'vehicle_locations'

# Simulated vehicle configuration
VEHICLES = [
    {'id': f'VEH{i:04d}', 'driver': f'DRV{i:04d}', 'max_capacity': random.randint(50, 200)}
    for i in range(1, 101)  # 100 vehicles
]

# Initial locations (simulated near warehouses)
WAREHOUSE_LOCATIONS = [
    {'lat': 45.5017, 'lon': -73.5673, 'name': 'Montreal Warehouse'},
    {'lat': 45.5017, 'lon': -73.5673, 'name': 'Montreal Warehouse East'},
    {'lat': 45.5017, 'lon': -73.5673, 'name': 'Montreal Warehouse West'},
    {'lat': 45.5017, 'lon': -73.5673, 'name': 'Montreal Warehouse North'},
]

STATUSES = ['IDLE', 'LOADING', 'IN_TRANSIT', 'DELIVERING', 'RETURNING']


def generate_vehicle_location(vehicle):
    """Generate vehicle location data"""
    # Randomly select warehouse as starting point
    warehouse = random.choice(WAREHOUSE_LOCATIONS)
    
    # Simulate vehicle movement (simplified: random walk)
    lat = warehouse['lat'] + random.uniform(-0.5, 0.5)
    lon = warehouse['lon'] + random.uniform(-0.5, 0.5)
    
    # Set speed and capacity based on status
    status = random.choice(STATUSES)
    if status == 'IDLE':
        speed = random.uniform(0, 10)
        capacity = 0
    elif status == 'LOADING':
        speed = 0
        capacity = random.randint(0, vehicle['max_capacity'] // 2)
    elif status == 'IN_TRANSIT':
        speed = random.uniform(30, 80)
        capacity = random.randint(vehicle['max_capacity'] // 2, vehicle['max_capacity'])
    elif status == 'DELIVERING':
        speed = random.uniform(20, 60)
        capacity = random.randint(1, vehicle['max_capacity'] // 2)
    else:  # RETURNING
        speed = random.uniform(40, 70)
        capacity = random.randint(0, vehicle['max_capacity'] // 4)
    
    location = {
        'vehicle_id': vehicle['id'],
        'driver_id': vehicle['driver'],
        'timestamp': int(time.time() * 1000),
        'latitude': lat,
        'longitude': lon,
        'speed_kmh': speed,
        'heading': random.uniform(0, 360),
        'status': status,
        'current_capacity': capacity,
        'max_capacity': vehicle['max_capacity'],
        'fuel_level': random.uniform(20, 100)
    }
    
    return location


def delivery_report(err, msg):
    """Kafka message delivery callback"""
    if err is not None:
        print(f'Message delivery failed: {err}')


def main():
    """Main function"""
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'vehicle-location-simulator'
    })
    
    print(f"Starting to send vehicle location data to topic: {TOPIC}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            # Update location for each vehicle every second
            for vehicle in VEHICLES:
                location = generate_vehicle_location(vehicle)
                
                producer.produce(
                    TOPIC,
                    key=vehicle['id'],
                    value=json.dumps(location),
                    callback=delivery_report
                )
            
            producer.poll(0)
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        producer.flush()
        print("Stopped sending")


if __name__ == '__main__':
    main()

