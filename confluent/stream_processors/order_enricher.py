#!/usr/bin/env python3
"""
OrderData富化Process器
从Kafka读取Order流，添加地理编码和Time特征，Send到enriched_orders topic
"""

import json
import time
from confluent_kafka import Consumer, Producer
from geopy.geocoders import Nominatim
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')
INPUT_TOPIC = 'orders'
OUTPUT_TOPIC = 'enriched_orders'

# Geocoder（Production environment should use缓存）
geolocator = Nominatim(user_agent="amazon-logistics")


def enrich_order(order_data):
    """富化OrderData"""
    enriched = order_data.copy()
    
    # 添加Time特征
    timestamp = order_data.get('timestamp', int(time.time() * 1000))
    dt = datetime.fromtimestamp(timestamp / 1000)
    
    enriched['day_of_week'] = dt.weekday()  # 0=Monday, 6=Sunday
    enriched['hour_of_day'] = dt.hour
    enriched['is_weekend'] = dt.weekday() >= 5
    enriched['is_peak_hour'] = 8 <= dt.hour <= 10 or 17 <= dt.hour <= 19
    
    # Add geographic features
    address = order_data.get('delivery_address', {})
    lat = address.get('latitude')
    lon = address.get('longitude')
    city = address.get('city', '')
    
    if lat and lon:
        # Calculate region（简化：Based on coordinates）
        if lat > 35:
            enriched['region'] = 'NORTH'
        elif lat < 25:
            enriched['region'] = 'SOUTH'
        else:
            enriched['region'] = 'CENTRAL'
        
        # 计算Delivery区域代码（简化）
        enriched['delivery_zone'] = f"{city}_{int(lat * 10)}_{int(lon * 10)}"
    
    # 添加Order特征
    items = order_data.get('items', [])
    enriched['total_items'] = len(items)
    enriched['total_weight'] = sum(item.get('weight_kg', 0) * item.get('quantity', 1) for item in items)
    enriched['total_volume'] = sum(
        item.get('dimensions', {}).get('length_cm', 0) *
        item.get('dimensions', {}).get('width_cm', 0) *
        item.get('dimensions', {}).get('height_cm', 0) *
        item.get('quantity', 1) / 1000000  # 转换为立方米
        for item in items
    )
    
    # 计算期望Delivery时长
    preferred_time = order_data.get('preferred_delivery_time')
    if preferred_time:
        enriched['expected_delivery_duration_ms'] = preferred_time - timestamp
        enriched['expected_delivery_duration_hours'] = (preferred_time - timestamp) / 3600000
    
    # 添加富化Time戳
    enriched['enrichment_timestamp'] = int(time.time() * 1000)
    
    return enriched


def main():
    """Main function"""
    # Create消费者
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'order-enricher',
        'auto.offset.reset': 'latest'
    })
    consumer.subscribe([INPUT_TOPIC])
    
    # Create生产者
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'order-enricher'
    })
    
    print(f"StartingProcessOrderData: {INPUT_TOPIC} -> {OUTPUT_TOPIC}")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"消费者Error: {msg.error()}")
                continue
            
            try:
                # 解析OrderData
                order_data = json.loads(msg.value().decode('utf-8'))
                
                # 富化Data
                enriched_order = enrich_order(order_data)
                
                # Send到输出topic
                producer.produce(
                    OUTPUT_TOPIC,
                    key=order_data.get('order_id', '').encode('utf-8'),
                    value=json.dumps(enriched_order).encode('utf-8')
                )
                producer.poll(0)
                
                print(f"Enriched order: {order_data.get('order_id')}")
                
            except json.JSONDecodeError as e:
                print(f"JSON解析Error: {e}")
            except Exception as e:
                print(f"ProcessError: {e}")
                
    except KeyboardInterrupt:
        print("\nIn progressStop...")
    finally:
        consumer.close()
        producer.flush()
        print("AlreadyStopProcess")


if __name__ == '__main__':
    main()

