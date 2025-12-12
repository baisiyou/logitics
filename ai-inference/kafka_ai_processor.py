#!/usr/bin/env python3
"""
Kafka AIProcess器
从Kafka读取Data，调用AI模型进行Prediction和检测，将结果写回Kafka
"""

import json
import time
from confluent_kafka import Consumer, Producer
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8000')

# Kafka Topics
INPUT_TOPICS = {
    'orders': 'enriched_orders',
    'vehicles': 'vehicles_with_traffic',
    'warehouses': 'warehouse_inventory_levels'
}

OUTPUT_TOPICS = {
    'demand_predictions': 'demand_predictions',
    'warehouse_pressure': 'warehouse_pressure_alerts',
    'eta_updates': 'eta_updates',
    'anomalies': 'anomaly_alerts'
}


def call_ai_service(endpoint: str, data: dict) -> dict:
    """调用AIServiceAPI"""
    try:
        response = requests.post(
            f"{AI_SERVICE_URL}{endpoint}",
            json=data,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"AIService调用Error: {e}")
        return None


def process_order(order_data: dict, producer: Producer):
    """ProcessOrderData：DemandPrediction和Anomaly检测"""
    # DemandPrediction（Simplified: based on city and region）
    city = order_data.get('city', '')
    region = order_data.get('region', '')
    hour = order_data.get('hour_of_day', 12)
    day = order_data.get('day_of_week', 1)
    
    # 调用DemandPredictionAPI（实际应聚合历史Data）
    prediction_request = {
        'city': city,
        'region': region,
        'hour_of_day': hour,
        'day_of_week': day,
        'historical_orders': []  # 实际应从历史Data获取
    }
    
    prediction = call_ai_service('/api/v1/predict/demand', prediction_request)
    if prediction:
        prediction['city'] = city
        prediction['region'] = region
        prediction['timestamp'] = int(time.time() * 1000)
        
        producer.produce(
            OUTPUT_TOPICS['demand_predictions'],
            key=f"{city}_{region}".encode('utf-8'),
            value=json.dumps(prediction).encode('utf-8')
        )
    
    # Anomaly检测
    anomaly_request = {
        'entity_type': 'order',
        'features': {
            'item_count': order_data.get('total_items', 0),
            'total_weight': order_data.get('total_weight', 0),
            'priority': order_data.get('priority', 'STANDARD')
        }
    }
    
    anomaly = call_ai_service('/api/v1/detect/anomaly', anomaly_request)
    if anomaly and anomaly.get('is_anomaly'):
        anomaly['order_id'] = order_data.get('order_id')
        anomaly['timestamp'] = int(time.time() * 1000)
        
        producer.produce(
            OUTPUT_TOPICS['anomalies'],
            key=order_data.get('order_id', '').encode('utf-8'),
            value=json.dumps(anomaly).encode('utf-8')
        )


def process_vehicle(vehicle_data: dict, producer: Producer):
    """ProcessVehicleData：ETAUpdate和Anomaly检测"""
    vehicle_id = vehicle_data.get('vehicle_id')
    current_location = vehicle_data.get('vehicle_location', {})
    traffic_info = vehicle_data.get('traffic_info', {})
    
    # ETAUpdate（Need destination information, simplified here）
    if current_location and traffic_info:
        eta_request = {
            'vehicle_id': vehicle_id,
            'current_location': {
                'latitude': current_location.get('latitude', 0),
                'longitude': current_location.get('longitude', 0)
            },
            'destination': {
                'latitude': current_location.get('latitude', 0) + 0.1,  # 简化
                'longitude': current_location.get('longitude', 0) + 0.1
            },
            'current_speed': vehicle_data.get('adjusted_speed_kmh', 50),
            'traffic_conditions': {
                'congestion_percentage': traffic_info.get('congestion_percentage', 0),
                'traffic_level': traffic_info.get('traffic_level', 'NORMAL')
            },
            'remaining_stops': 5  # 简化
        }
        
        eta_result = call_ai_service('/api/v1/calculate/eta', eta_request)
        if eta_result:
            eta_result['vehicle_id'] = vehicle_id
            eta_result['timestamp'] = int(time.time() * 1000)
            
            producer.produce(
                OUTPUT_TOPICS['eta_updates'],
                key=vehicle_id.encode('utf-8'),
                value=json.dumps(eta_result).encode('utf-8')
            )
    
    # Anomaly检测
    anomaly_request = {
        'entity_type': 'vehicle',
        'features': {
            'fuel_level': vehicle_data.get('fuel_level', 100),
            'speed_kmh': vehicle_data.get('adjusted_speed_kmh', 0),
            'status': vehicle_data.get('status', ''),
            'capacity_ratio': vehicle_data.get('utilization_percentage', 0) / 100
        }
    }
    
    anomaly = call_ai_service('/api/v1/detect/anomaly', anomaly_request)
    if anomaly and anomaly.get('is_anomaly'):
        anomaly['vehicle_id'] = vehicle_id
        anomaly['timestamp'] = int(time.time() * 1000)
        
        producer.produce(
            OUTPUT_TOPICS['anomalies'],
            key=vehicle_id.encode('utf-8'),
            value=json.dumps(anomaly).encode('utf-8')
        )


def process_warehouse(warehouse_data: dict, producer: Producer):
    """ProcessWarehouseData：PressurePrediction"""
    warehouse_id = warehouse_data.get('warehouse_id')
    
    pressure_request = {
        'warehouse_id': warehouse_id,
        'current_orders': warehouse_data.get('current_stock', 0),
        'current_capacity': 1000,  # 简化：假设容量
        'pending_orders': warehouse_data.get('reserved_stock', 0),
        'historical_data': []
    }
    
    pressure = call_ai_service('/api/v1/predict/warehouse-pressure', pressure_request)
    if pressure and pressure.get('pressure_level') in ['HIGH', 'CRITICAL']:
        pressure['timestamp'] = int(time.time() * 1000)
        
        producer.produce(
            OUTPUT_TOPICS['warehouse_pressure'],
            key=warehouse_id.encode('utf-8'),
            value=json.dumps(pressure).encode('utf-8')
        )


def main():
    """Main function"""
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'kafka-ai-processor',
        'auto.offset.reset': 'earliest'  # 从最早的消息开始读取，确保不遗漏数据
    })
    
    # Subscribe to all input topics
    topics = list(INPUT_TOPICS.values())
    consumer.subscribe(topics)
    
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'kafka-ai-processor'
    })
    
    print(f"StartingAIProcess: {topics}")
    print(f"AIService地址: {AI_SERVICE_URL}")
    
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
                
                if topic == INPUT_TOPICS['orders']:
                    process_order(data, producer)
                elif topic == INPUT_TOPICS['vehicles']:
                    process_vehicle(data, producer)
                elif topic == INPUT_TOPICS['warehouses']:
                    process_warehouse(data, producer)
                
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

