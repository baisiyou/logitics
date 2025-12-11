#!/usr/bin/env python3
"""
流-流关联Process器
关联Order和库存Data，Vehicle和交通Data
"""

import json
import time
from confluent_kafka import Consumer, Producer
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')

# State storage（Production environment should useRedis或Kafka StreamsState storage）
inventory_state = defaultdict(dict)  # {warehouse_id: {product_id: stock_info}}
traffic_state = defaultdict(dict)  # {location_key: traffic_info}


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points（kilometers）- Simplified Haversine formula"""
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Earth radius（kilometers）
    return c * r


def join_order_inventory(order_data):
    """关联Order和库存"""
    items = order_data.get('items', [])
    address = order_data.get('delivery_address', {})
    city = address.get('city', '')
    
    # 查找最近Warehouse的库存
    matched_items = []
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)
        
        # 查找有库存的Warehouse（简化：Match based on city）
        best_match = None
        best_stock = 0
        
        for warehouse_id, products in inventory_state.items():
            if product_id in products:
                stock_info = products[product_id]
                available = stock_info.get('available_stock', 0)
                
                if available >= quantity and available > best_stock:
                    best_stock = available
                    best_match = {
                        'warehouse_id': warehouse_id,
                        'product_id': product_id,
                        'available_stock': available,
                        'current_stock': stock_info.get('current_stock', 0)
                    }
        
        matched_items.append({
            'item': item,
            'inventory_match': best_match,
            'stock_status': 'IN_STOCK' if best_match else 'OUT_OF_STOCK'
        })
    
    return {
        'order_id': order_data.get('order_id'),
        'customer_id': order_data.get('customer_id'),
        'delivery_city': city,
        'items_with_inventory': matched_items,
        'timestamp': int(time.time() * 1000)
    }


def join_vehicle_traffic(vehicle_data):
    """关联Vehicle和交通Data"""
    vehicle_lat = vehicle_data.get('latitude')
    vehicle_lon = vehicle_data.get('longitude')
    
    if not vehicle_lat or not vehicle_lon:
        return None
    
    # 查找最近的交通Data（简化：Based on coordinate grid）
    location_key = f"{int(vehicle_lat * 100)}_{int(vehicle_lon * 100)}"
    
    # 查找附近交通Data
    best_traffic = None
    min_distance = float('inf')
    
    for traffic_key, traffic_info in traffic_state.items():
        traffic_lat = traffic_info.get('latitude')
        traffic_lon = traffic_info.get('longitude')
        
        if traffic_lat and traffic_lon:
            distance = calculate_distance(vehicle_lat, vehicle_lon, traffic_lat, traffic_lon)
            
            if distance < 5 and distance < min_distance:  # Within 5 km
                min_distance = distance
                best_traffic = traffic_info.copy()
                best_traffic['distance_km'] = distance
    
    if best_traffic:
        # Calculate adjusted ETA
        vehicle_speed = vehicle_data.get('speed_kmh', 50)
        traffic_speed = best_traffic.get('speed_kmh', vehicle_speed)
        
        # Adjust using traffic speed
        adjusted_speed = min(vehicle_speed, traffic_speed)
        
        return {
            'vehicle_id': vehicle_data.get('vehicle_id'),
            'driver_id': vehicle_data.get('driver_id'),
            'vehicle_location': {
                'latitude': vehicle_lat,
                'longitude': vehicle_lon
            },
            'traffic_info': best_traffic,
            'adjusted_speed_kmh': adjusted_speed,
            'congestion_impact': best_traffic.get('congestion_percentage', 0),
            'timestamp': int(time.time() * 1000)
        }
    
    return None


def main():
    """Main function"""
    # Create消费者（订阅多个topic）
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'stream-joiner',
        'auto.offset.reset': 'latest'
    })
    consumer.subscribe(['orders', 'inventory_updates', 'vehicle_locations', 'traffic_updates'])
    
    # Create生产者
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'stream-joiner'
    })
    
    print("Starting流-流关联Process")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"消费者Error: {msg.error()}")
                continue
            
            topic = msg.topic()
            
            try:
                data = json.loads(msg.value().decode('utf-8'))
                
                if topic == 'inventory_updates':
                    # Update库存Status
                    warehouse_id = data.get('warehouse_id')
                    product_id = data.get('product_id')
                    if warehouse_id and product_id:
                        inventory_state[warehouse_id][product_id] = {
                            'current_stock': data.get('current_stock', 0),
                            'available_stock': data.get('available_stock', 0),
                            'reserved_stock': data.get('reserved_stock', 0),
                            'timestamp': data.get('timestamp', int(time.time() * 1000))
                        }
                
                elif topic == 'traffic_updates':
                    # Update交通Status
                    location_key = f"{int(data.get('latitude', 0) * 100)}_{int(data.get('longitude', 0) * 100)}"
                    traffic_state[location_key] = data
                    # 清理旧Data（超过10minutes）
                    current_time = int(time.time() * 1000)
                    traffic_state[location_key]['_timestamp'] = current_time
                    traffic_state = {
                        k: v for k, v in traffic_state.items()
                        if current_time - v.get('_timestamp', 0) < 600000
                    }
                
                elif topic == 'orders':
                    # 关联Order和库存
                    joined = join_order_inventory(data)
                    if joined:
                        producer.produce(
                            'orders_with_inventory',
                            key=data.get('order_id', '').encode('utf-8'),
                            value=json.dumps(joined).encode('utf-8')
                        )
                        producer.poll(0)
                
                elif topic == 'vehicle_locations':
                    # 关联Vehicle和交通
                    joined = join_vehicle_traffic(data)
                    if joined:
                        producer.produce(
                            'vehicles_with_traffic',
                            key=data.get('vehicle_id', '').encode('utf-8'),
                            value=json.dumps(joined).encode('utf-8')
                        )
                        producer.poll(0)
                
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

