#!/usr/bin/env python3
"""
Dispatch指挥中心
Real-time监控和IntelligentDispatch决策
"""

import json
import time
import random
from typing import Dict, List, Any
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from collections import defaultdict
import asyncio

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')
CONFLUENT_API_KEY = os.getenv('CONFLUENT_API_KEY', None)
CONFLUENT_API_SECRET = os.getenv('CONFLUENT_API_SECRET', None)

app = FastAPI(title="Amazon Logistics Dispatch Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Real-timeState storage
dispatch_state = {
    'orders': {},
    'vehicles': {},
    'warehouses': {},
    'demand_predictions': {},
    'alerts': [],
    'statistics': {
        'total_orders_today': 0,
        'active_vehicles': 0,
        'delivered_today': 0,
        'pending_orders': 0
    }
}

# WebSocket connection management
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


def generate_mock_data():
    """生成初始模拟数据用于演示（当没有 Kafka 数据源时）"""
    cities = ['Montreal', 'Toronto', 'Vancouver', 'Calgary', 'Ottawa']
    priorities = ['STANDARD', 'EXPRESS', 'SAME_DAY']
    current_time = int(time.time() * 1000)
    
    # 生成模拟订单
    for i in range(random.randint(5, 15)):
        order_id = f"ORD{int(time.time() * 1000)}{i}"
        city = random.choice(cities)
        priority = random.choice(priorities)
        
        # 设置预计交付时间
        if priority == 'SAME_DAY':
            preferred_time = current_time + random.randint(3600000, 7200000)  # 1-2小时
        elif priority == 'EXPRESS':
            preferred_time = current_time + random.randint(7200000, 14400000)  # 2-4小时
        else:
            preferred_time = current_time + random.randint(14400000, 86400000)  # 4-24小时
        
        dispatch_state['orders'][order_id] = {
            'order_id': order_id,
            'customer_id': f"CUST{random.randint(10000, 99999)}",
            'timestamp': current_time - random.randint(0, 3600000),
            'delivery_address': {
                'city': city,
                'latitude': 45.5017 + random.uniform(-0.1, 0.1),
                'longitude': -73.5673 + random.uniform(-0.1, 0.1)
            },
            'priority': priority,
            'preferred_delivery_time': preferred_time,
            'items': [{'product_id': f'P{random.randint(1, 5)}', 'quantity': random.randint(1, 3)}]
        }
    
    # 生成模拟车辆
    for i in range(random.randint(8, 20)):
        vehicle_id = f"VEH{i+1:04d}"
        status = random.choice(['IDLE', 'LOADING', 'IN_TRANSIT', 'DELIVERING'])
        dispatch_state['vehicles'][vehicle_id] = {
            'vehicle_id': vehicle_id,
            'driver_id': f'DRV{i+1:04d}',
            'timestamp': int(time.time() * 1000),
            'latitude': 45.5017 + random.uniform(-0.3, 0.3),
            'longitude': -73.5673 + random.uniform(-0.3, 0.3),
            'speed_kmh': random.uniform(0, 80) if status != 'IDLE' else 0,
            'status': status,
            'current_capacity': random.randint(0, 100),
            'max_capacity': random.randint(100, 200),
            'fuel_level': random.uniform(30, 100)
        }
    
    # 生成模拟仓库
    for i in range(3):
        warehouse_id = f"WH{i+1:03d}"
        dispatch_state['warehouses'][warehouse_id] = {
            'warehouse_id': warehouse_id,
            'name': f"Warehouse {i+1}",
            'latitude': 45.5017 + random.uniform(-0.2, 0.2),
            'longitude': -73.5673 + random.uniform(-0.2, 0.2),
            'capacity': random.randint(1000, 5000),
            'current_inventory': random.randint(500, 4500)
        }
    
    # 初始化统计数据（初始时 delivered_today 为 0）
    dispatch_state['statistics'] = {
        'total_orders_today': len(dispatch_state['orders']),
        'active_vehicles': len([v for v in dispatch_state['vehicles'].values() if v.get('status') in ['IN_TRANSIT', 'DELIVERING']]),
        'delivered_today': 0,
        'pending_orders': len([o for o in dispatch_state['orders'].values()])
    }
    
    print(f"生成模拟数据: {len(dispatch_state['orders'])} 订单, {len(dispatch_state['vehicles'])} 车辆")


def update_statistics():
    """更新统计数据"""
    # 保留 delivered_today 的值（如果已存在）
    current_delivered = dispatch_state['statistics'].get('delivered_today', 0)
    
    dispatch_state['statistics'] = {
        'total_orders_today': len(dispatch_state['orders']) + current_delivered,  # 包括已交付的订单
        'active_vehicles': len([v for v in dispatch_state['vehicles'].values() if v.get('status') in ['IN_TRANSIT', 'DELIVERING']]),
        'delivered_today': current_delivered,
        'pending_orders': len([o for o in dispatch_state['orders'].values()])
    }


def simulate_new_order():
    """模拟新订单到达"""
    cities = ['Montreal', 'Toronto', 'Vancouver', 'Calgary', 'Ottawa']
    priorities = ['STANDARD', 'EXPRESS', 'SAME_DAY']
    current_time = int(time.time() * 1000)
    
    order_id = f"ORD{int(time.time() * 1000)}{random.randint(1000, 9999)}"
    city = random.choice(cities)
    priority = random.choice(priorities)
    
    # 设置预计交付时间
    if priority == 'SAME_DAY':
        preferred_time = current_time + random.randint(3600000, 7200000)  # 1-2小时
    elif priority == 'EXPRESS':
        preferred_time = current_time + random.randint(7200000, 14400000)  # 2-4小时
    else:
        preferred_time = current_time + random.randint(14400000, 86400000)  # 4-24小时
    
    dispatch_state['orders'][order_id] = {
        'order_id': order_id,
        'customer_id': f"CUST{random.randint(10000, 99999)}",
        'timestamp': current_time,
        'delivery_address': {
            'city': city,
            'latitude': 45.5017 + random.uniform(-0.1, 0.1),
            'longitude': -73.5673 + random.uniform(-0.1, 0.1)
        },
        'priority': priority,
        'preferred_delivery_time': preferred_time,
        'items': [{'product_id': f'P{random.randint(1, 5)}', 'quantity': random.randint(1, 3)}]
    }
    
    update_statistics()
    
    # 广播新订单
    asyncio.create_task(manager.broadcast({
        'type': 'order_assigned',
        'data': {
            'order_id': order_id,
            'assigned_vehicle': random.choice(list(dispatch_state['vehicles'].keys())) if dispatch_state['vehicles'] else None,
            'timestamp': current_time
        }
    }))
    
    print(f"模拟新订单: {order_id}")


def simulate_vehicle_update():
    """模拟车辆位置和状态更新"""
    if not dispatch_state['vehicles']:
        return
    
    vehicle_id = random.choice(list(dispatch_state['vehicles'].keys()))
    vehicle = dispatch_state['vehicles'][vehicle_id]
    
    # 随机更新车辆状态
    current_status = vehicle.get('status', 'IDLE')
    if random.random() < 0.3:  # 30% 概率改变状态
        status_options = ['IDLE', 'LOADING', 'IN_TRANSIT', 'DELIVERING', 'RETURNING']
        current_status = random.choice(status_options)
        vehicle['status'] = current_status
    
    # 更新位置（模拟移动）
    vehicle['latitude'] += random.uniform(-0.01, 0.01)
    vehicle['longitude'] += random.uniform(-0.01, 0.01)
    vehicle['timestamp'] = int(time.time() * 1000)
    vehicle['speed_kmh'] = random.uniform(0, 80) if current_status not in ['IDLE', 'LOADING'] else 0
    vehicle['fuel_level'] = max(0, vehicle.get('fuel_level', 100) - random.uniform(0, 0.5))
    
    update_statistics()


def simulate_delivery():
    """模拟订单完成（交付）"""
    if not dispatch_state['orders']:
        return
    
    # 随机选择一个订单标记为已完成
    order_id = random.choice(list(dispatch_state['orders'].keys()))
    
    # 模拟交付：增加已交付数量，移除订单
    current_delivered = dispatch_state['statistics'].get('delivered_today', 0)
    dispatch_state['statistics']['delivered_today'] = current_delivered + 1
    dispatch_state['orders'].pop(order_id, None)
    
    # 更新其他统计
    dispatch_state['statistics']['pending_orders'] = len(dispatch_state['orders'])
    # total_orders_today 保持不变（因为它应该包括已交付的订单）
    
    print(f"模拟订单交付: {order_id}, 已交付总数: {dispatch_state['statistics']['delivered_today']}")


def generate_alert(alert_type: str, severity: str, description: str, data: dict = None):
    """生成警报并广播"""
    alert = {
        'type': alert_type,
        'severity': severity,  # LOW, MEDIUM, HIGH, CRITICAL
        'description': description,
        'timestamp': int(time.time() * 1000),
        'data': data or {}
    }
    
    # 添加到警报列表
    dispatch_state['alerts'].append(alert)
    
    # 只保留最近100条警报
    if len(dispatch_state['alerts']) > 100:
        dispatch_state['alerts'] = dispatch_state['alerts'][-100:]
    
    # 通过WebSocket广播警报
    asyncio.create_task(manager.broadcast({
        'type': 'alert',
        'data': alert
    }))
    
    print(f"生成警报: [{severity}] {description}")
    return alert


def check_and_generate_alerts():
    """检查各种条件并生成警报"""
    # 1. 检查车辆低油量
    for vehicle_id, vehicle in dispatch_state['vehicles'].items():
        fuel_level = vehicle.get('fuel_level', 100)
        if fuel_level < 20:
            severity = 'CRITICAL' if fuel_level < 10 else 'HIGH'
            generate_alert(
                'low_fuel',
                severity,
                f"车辆 {vehicle_id} 油量低 ({fuel_level:.1f}%)",
                {
                    'vehicle_id': vehicle_id,
                    'driver_id': vehicle.get('driver_id'),
                    'fuel_level': fuel_level,
                    'location': {'lat': vehicle.get('latitude'), 'lon': vehicle.get('longitude')}
                }
            )
    
    # 2. 检查订单延迟（超过预计交付时间）
    current_time = int(time.time() * 1000)
    for order_id, order in list(dispatch_state['orders'].items()):
        # 如果订单存在 preferred_delivery_time，检查是否延迟
        if 'preferred_delivery_time' in order:
            preferred_time = order.get('preferred_delivery_time')
            if current_time > preferred_time:
                delay_minutes = (current_time - preferred_time) // 60000
                severity = 'CRITICAL' if delay_minutes > 60 else 'HIGH' if delay_minutes > 30 else 'MEDIUM'
                generate_alert(
                    'delayed_delivery',
                    severity,
                    f"订单 {order_id} 延迟交付 ({delay_minutes} 分钟)",
                    {
                        'order_id': order_id,
                        'customer_id': order.get('customer_id'),
                        'delay_minutes': delay_minutes,
                        'priority': order.get('priority'),
                        'city': order.get('delivery_address', {}).get('city')
                    }
                )
        else:
            # 如果没有 preferred_delivery_time，检查订单创建时间（超过2小时未处理）
            order_time = order.get('timestamp', current_time)
            age_hours = (current_time - order_time) / 3600000
            if age_hours > 2:
                generate_alert(
                    'pending_order_timeout',
                    'HIGH',
                    f"订单 {order_id} 待处理时间过长 ({age_hours:.1f} 小时)",
                    {
                        'order_id': order_id,
                        'customer_id': order.get('customer_id'),
                        'age_hours': age_hours,
                        'priority': order.get('priority')
                    }
                )
    
    # 3. 检查高优先级订单积压
    high_priority_orders = [
        o for o in dispatch_state['orders'].values()
        if o.get('priority') in ['EXPRESS', 'SAME_DAY']
    ]
    if len(high_priority_orders) > 10:
        generate_alert(
            'high_priority_backlog',
            'HIGH',
            f"高优先级订单积压 ({len(high_priority_orders)} 单待处理)",
            {
                'count': len(high_priority_orders),
                'express_count': len([o for o in high_priority_orders if o.get('priority') == 'EXPRESS']),
                'same_day_count': len([o for o in high_priority_orders if o.get('priority') == 'SAME_DAY'])
            }
        )
    
    # 4. 检查仓库库存不足
    for warehouse_id, warehouse in dispatch_state['warehouses'].items():
        capacity = warehouse.get('capacity', 1000)
        current_inventory = warehouse.get('current_inventory', 500)
        utilization = current_inventory / capacity if capacity > 0 else 0
        
        if utilization < 0.1:  # 库存低于10%
            generate_alert(
                'low_inventory',
                'HIGH',
                f"仓库 {warehouse_id} 库存不足 ({utilization*100:.1f}%)",
                {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse.get('name'),
                    'current_inventory': current_inventory,
                    'capacity': capacity,
                    'utilization': utilization
                }
            )
        elif utilization > 0.9:  # 库存高于90%
            generate_alert(
                'high_inventory',
                'MEDIUM',
                f"仓库 {warehouse_id} 库存接近满载 ({utilization*100:.1f}%)",
                {
                    'warehouse_id': warehouse_id,
                    'warehouse_name': warehouse.get('name'),
                    'current_inventory': current_inventory,
                    'capacity': capacity,
                    'utilization': utilization
                }
            )
    
    # 5. 检查车辆异常状态
    idle_vehicles = [v for v in dispatch_state['vehicles'].values() if v.get('status') == 'IDLE']
    total_vehicles = len(dispatch_state['vehicles'])
    if total_vehicles > 0:
        idle_ratio = len(idle_vehicles) / total_vehicles
        if idle_ratio > 0.5 and len(dispatch_state['orders']) > 5:
            generate_alert(
                'excessive_idle_vehicles',
                'MEDIUM',
                f"大量车辆闲置 ({len(idle_vehicles)}/{total_vehicles})，但仍有订单待处理",
                {
                    'idle_count': len(idle_vehicles),
                    'total_count': total_vehicles,
                    'pending_orders': len(dispatch_state['orders'])
                }
            )
    
    # 6. 检查车辆速度异常（可能表示故障或交通问题）
    for vehicle_id, vehicle in dispatch_state['vehicles'].items():
        if vehicle.get('status') in ['IN_TRANSIT', 'DELIVERING']:
            speed = vehicle.get('speed_kmh', 0)
            # 如果状态是在运输中但速度为0，可能是故障
            if speed == 0 and vehicle.get('status') == 'IN_TRANSIT':
                generate_alert(
                    'vehicle_stalled',
                    'HIGH',
                    f"车辆 {vehicle_id} 可能在运输中停滞",
                    {
                        'vehicle_id': vehicle_id,
                        'driver_id': vehicle.get('driver_id'),
                        'status': vehicle.get('status'),
                        'location': {'lat': vehicle.get('latitude'), 'lon': vehicle.get('longitude')}
                    }
                )


def mock_data_simulator_loop():
    """模拟数据生成循环（当没有 Kafka 时）"""
    print("模拟数据生成器线程已启动")
    initial_delay = 3  # 首次延迟3秒
    time.sleep(initial_delay)
    
    while True:
        try:
            # 每5秒执行一次（更频繁的更新）
            time.sleep(5)
            
            # 50% 概率生成新订单（提高概率让变化更明显）
            if random.random() < 0.5:
                simulate_new_order()
            
            # 每次更新车辆位置
            simulate_vehicle_update()
            
            # 30% 概率模拟订单交付（提高概率）
            if random.random() < 0.3 and dispatch_state['orders']:
                simulate_delivery()
            
            # 每次循环检查并生成警报（20%概率，避免警报过多）
            if random.random() < 0.2:
                check_and_generate_alerts()
            
            # 定期打印状态（用于调试）
            if random.random() < 0.1:  # 10% 概率打印状态
                stats = dispatch_state['statistics']
                print(f"当前状态: 订单={stats.get('total_orders_today', 0)}, "
                      f"活跃车辆={stats.get('active_vehicles', 0)}, "
                      f"已交付={stats.get('delivered_today', 0)}, "
                      f"待处理={stats.get('pending_orders', 0)}")
                
        except Exception as e:
            print(f"模拟数据生成错误: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


def optimize_dispatch(order: Dict, vehicles: Dict, warehouses: Dict) -> Dict[str, Any]:
    """
    IntelligentDispatch优化算法
    匹配Order、Vehicle和Warehouse
    """
    order_location = order.get('delivery_address', {})
    order_lat = order_location.get('latitude', 0)
    order_lon = order_location.get('longitude', 0)
    priority = order.get('priority', 'STANDARD')
    
    # 1. 选择最近的有库存Warehouse
    best_warehouse = None
    min_warehouse_distance = float('inf')
    
    for warehouse_id, warehouse in warehouses.items():
        wh_lat = warehouse.get('latitude', 0)
        wh_lon = warehouse.get('longitude', 0)
        
        # 简化距离计算
        distance = abs(order_lat - wh_lat) + abs(order_lon - wh_lon)
        
        if distance < min_warehouse_distance:
            min_warehouse_distance = distance
            best_warehouse = warehouse_id
    
    # 2. 选择最优Vehicle
    best_vehicle = None
    best_score = -1
    
    for vehicle_id, vehicle in vehicles.items():
        if vehicle.get('status') not in ['IDLE', 'LOADING']:
            continue
        
        vehicle_lat = vehicle.get('latitude', 0)
        vehicle_lon = vehicle.get('longitude', 0)
        
        # 计算到Warehouse的距离
        to_warehouse_dist = abs(vehicle_lat - warehouses.get(best_warehouse, {}).get('latitude', 0)) + \
                           abs(vehicle_lon - warehouses.get(best_warehouse, {}).get('longitude', 0))
        
        # Calculate distance to destination
        to_dest_dist = abs(vehicle_lat - order_lat) + abs(vehicle_lon - order_lon)
        
        # Calculate comprehensive score（Distance, capacity, priority matching）
        capacity_ratio = vehicle.get('current_capacity', 0) / max(vehicle.get('max_capacity', 1), 1)
        fuel_level = vehicle.get('fuel_level', 100)
        
        # 优先级匹配：ExpressOrder优先分配给IdleVehicle
        priority_bonus = 1.0
        if priority == 'SAME_DAY' and vehicle.get('status') == 'IDLE':
            priority_bonus = 2.0
        elif priority == 'EXPRESS' and vehicle.get('status') == 'IDLE':
            priority_bonus = 1.5
        
        score = priority_bonus / (to_warehouse_dist + to_dest_dist + 1) * \
                (1 - capacity_ratio) * (fuel_level / 100)
        
        if score > best_score:
            best_score = score
            best_vehicle = vehicle_id
    
    return {
        'order_id': order.get('order_id'),
        'assigned_warehouse': best_warehouse,
        'assigned_vehicle': best_vehicle,
        'estimated_pickup_time': int(time.time() + 30 * 60) * 1000,  # 30minutes后
        'estimated_delivery_time': int(time.time() + 120 * 60) * 1000,  # 2hours后
        'priority': priority,
        'score': best_score,
        'timestamp': int(time.time() * 1000)
    }


def kafka_consumer_loop():
    """Kafka consumer loop（Run in background）"""
    topics = [
        'orders',
        'vehicle_locations',
        'warehouse_inventory_levels',
        'demand_predictions',
        'anomaly_alerts',
        'warehouse_pressure_alerts'
    ]
    
    # 配置 Kafka 连接参数
    consumer_config = {
        'bootstrap_servers': BOOTSTRAP_SERVERS.split(','),  # 支持多个服务器
        'group_id': 'dispatch-center',
        'auto_offset_reset': 'earliest',  # 从最早的消息开始读取
        'value_deserializer': lambda m: json.loads(m.decode('utf-8')),
        'consumer_timeout_ms': 1000  # 1秒超时
    }
    
    producer_config = {
        'bootstrap_servers': BOOTSTRAP_SERVERS.split(','),
        'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
        'key_serializer': lambda k: k.encode('utf-8') if k else None
    }
    
    # 如果提供了 Confluent Cloud 认证信息，添加 SASL 配置
    if CONFLUENT_API_KEY and CONFLUENT_API_SECRET:
        consumer_config.update({
            'security_protocol': 'SASL_SSL',
            'sasl_mechanism': 'PLAIN',
            'sasl_plain_username': CONFLUENT_API_KEY,
            'sasl_plain_password': CONFLUENT_API_SECRET
        })
        producer_config.update({
            'security_protocol': 'SASL_SSL',
            'sasl_mechanism': 'PLAIN',
            'sasl_plain_username': CONFLUENT_API_KEY,
            'sasl_plain_password': CONFLUENT_API_SECRET
        })
    
    # 使用 kafka-python 创建 consumer 和 producer
    try:
        consumer = KafkaConsumer(*topics, **consumer_config)
        producer = KafkaProducer(**producer_config)
        print("Dispatch中心Kafka消费者已启动")
    except Exception as e:
        print(f"Kafka连接失败: {e}")
        print("如果这是第一次启动且没有 Kafka 配置，这是正常的")
        # 如果还没有初始化模拟数据，则初始化
        if not dispatch_state['orders'] and not dispatch_state['vehicles']:
            print("初始化模拟数据作为备选方案...")
            generate_mock_data()
            # 启动模拟数据生成器
            import threading
            mock_simulator_thread = threading.Thread(target=mock_data_simulator_loop, daemon=True)
            mock_simulator_thread.start()
            print("模拟数据生成器已启动")
        return  # 如果 Kafka 连接失败，直接返回
    
    try:
        while True:
            try:
                # kafka-python 的 consumer 是一个迭代器
                # consumer_timeout_ms 设置超时，如果没有消息会抛出 StopIteration
                msg_pack = consumer.poll(timeout_ms=1000)
                
                if not msg_pack:
                    continue
                
                # msg_pack 是一个字典：{TopicPartition: [messages]}
                for topic_partition, messages in msg_pack.items():
                    for msg in messages:
                        topic = msg.topic
                        
                        try:
                            data = msg.value  # kafka-python 已经自动反序列化
                            
                            if topic == 'orders':
                                order_id = data.get('order_id')
                                dispatch_state['orders'][order_id] = data
                                dispatch_state['statistics']['total_orders_today'] += 1
                                dispatch_state['statistics']['pending_orders'] += 1
                                
                                # 执行Dispatch优化
                                assignment = optimize_dispatch(
                                    data,
                                    dispatch_state['vehicles'],
                                    dispatch_state['warehouses']
                                )
                                
                                # SendDispatch指令
                                producer.send(
                                    'dispatch_assignments',
                                    key=order_id,
                                    value=assignment
                                )
                                producer.flush()
                                
                                # 广播Update
                                asyncio.create_task(manager.broadcast({
                                    'type': 'order_assigned',
                                    'data': assignment
                                }))
                            
                            elif topic == 'vehicle_locations':
                                vehicle_id = data.get('vehicle_id')
                                dispatch_state['vehicles'][vehicle_id] = data
                                
                                if data.get('status') in ['IN_TRANSIT', 'DELIVERING']:
                                    dispatch_state['statistics']['active_vehicles'] = len([
                                        v for v in dispatch_state['vehicles'].values()
                                        if v.get('status') in ['IN_TRANSIT', 'DELIVERING']
                                    ])
                            
                            elif topic == 'warehouse_inventory_levels':
                                warehouse_id = data.get('warehouse_id')
                                dispatch_state['warehouses'][warehouse_id] = data
                            
                            elif topic == 'demand_predictions':
                                key = f"{data.get('city')}_{data.get('region')}"
                                dispatch_state['demand_predictions'][key] = data
                            
                            elif topic in ['anomaly_alerts', 'warehouse_pressure_alerts']:
                                alert = {
                                    'type': topic,
                                    'data': data,
                                    'timestamp': int(time.time() * 1000),
                                    'severity': data.get('severity', 'MEDIUM')
                                }
                                dispatch_state['alerts'].append(alert)
                                
                                # 只保留最近100条Alert
                                if len(dispatch_state['alerts']) > 100:
                                    dispatch_state['alerts'] = dispatch_state['alerts'][-100:]
                                
                                # 广播Alert
                                asyncio.create_task(manager.broadcast({
                                    'type': 'alert',
                                    'data': alert
                                }))
                            
                        except Exception as e:
                            print(f"ProcessError: {e}")
                                
            except StopIteration:
                # 超时，继续循环
                continue
            except Exception as e:
                print(f"Kafka consumer error: {e}")
                time.sleep(1)  # 出错时等待1秒再继续
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.close()


# Start后台Kafka消费者
import threading

# 检查是否应该使用模拟数据模式
# 如果 BOOTSTRAP_SERVERS 是默认值（localhost:9092）且没有设置 CONFLUENT_API_KEY，则使用模拟数据
USE_MOCK_DATA = (BOOTSTRAP_SERVERS == 'localhost:9092' and not CONFLUENT_API_KEY)

if USE_MOCK_DATA:
    print("=" * 50)
    print("未检测到 Kafka 配置，使用模拟数据模式")
    print("=" * 50)
    generate_mock_data()
    # 启动模拟数据生成器（定期更新数据）
    mock_simulator_thread = threading.Thread(target=mock_data_simulator_loop, daemon=True)
    mock_simulator_thread.start()
    print("模拟数据生成器已启动，数据将每5秒更新一次")
else:
    print(f"检测到 Kafka 配置: {BOOTSTRAP_SERVERS}")
    print("将尝试连接 Kafka...")

consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
consumer_thread.start()

# 如果 Kafka 连接失败，启动模拟数据生成器作为备选方案
# 这会在 kafka_consumer_loop 函数内部处理（通过返回或异常）


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，Real-time推送DispatchData"""
    await manager.connect(websocket)
    
    # Send初始Status
    await websocket.send_json({
        'type': 'initial_state',
        'data': dispatch_state
    })
    
    try:
        while True:
            # 保持连接，等待Customer端Message
            data = await websocket.receive_text()
            # 可以ProcessCustomer端请求
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/v1/status")
async def get_status():
    """获取当前DispatchStatus"""
    return dispatch_state


@app.get("/api/v1/orders")
async def get_orders():
    """获取所有Order"""
    return list(dispatch_state['orders'].values())


@app.get("/api/v1/vehicles")
async def get_vehicles():
    """获取所有VehicleStatus"""
    return list(dispatch_state['vehicles'].values())


@app.get("/api/v1/warehouses")
async def get_warehouses():
    """获取所有WarehouseStatus"""
    return list(dispatch_state['warehouses'].values())


@app.get("/api/v1/alerts")
async def get_alerts(limit: int = 50):
    """获取Alert列表"""
    return dispatch_state['alerts'][-limit:]


@app.get("/api/v1/statistics")
async def get_statistics():
    """Get statistics"""
    return dispatch_state['statistics']


@app.get("/api/v1/demand-predictions")
async def get_demand_predictions():
    """获取DemandPrediction"""
    return list(dispatch_state['demand_predictions'].values())


@app.post("/api/v1/generate-mock-data")
async def generate_mock_data_endpoint():
    """生成模拟数据（用于演示，不需要 Kafka）"""
    generate_mock_data()
    asyncio.create_task(manager.broadcast({
        'type': 'initial_state',
        'data': dispatch_state
    }))
    return {"success": True, "message": "模拟数据已生成", "data": dispatch_state}


@app.post("/api/v1/manual-dispatch")
async def manual_dispatch(order_id: str, vehicle_id: str):
    """手动Dispatch"""
    if order_id not in dispatch_state['orders']:
        return {"error": "Order不存在"}
    
    if vehicle_id not in dispatch_state['vehicles']:
        return {"error": "Vehicle不存在"}
    
    order = dispatch_state['orders'][order_id]
    vehicle = dispatch_state['vehicles'][vehicle_id]
    
    assignment = {
        'order_id': order_id,
        'assigned_vehicle': vehicle_id,
        'manual': True,
        'timestamp': int(time.time() * 1000)
    }
    
    # SendDispatch指令
    producer_config = {
        'bootstrap_servers': BOOTSTRAP_SERVERS.split(','),
        'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
        'key_serializer': lambda k: k.encode('utf-8') if k else None
    }
    
    # 如果提供了 Confluent Cloud 认证信息，添加 SASL 配置
    if CONFLUENT_API_KEY and CONFLUENT_API_SECRET:
        producer_config.update({
            'security_protocol': 'SASL_SSL',
            'sasl_mechanism': 'PLAIN',
            'sasl_plain_username': CONFLUENT_API_KEY,
            'sasl_plain_password': CONFLUENT_API_SECRET
        })
    
    producer = KafkaProducer(**producer_config)
    
    producer.send(
        'dispatch_assignments',
        key=order_id,
        value=assignment
    )
    producer.flush()
    producer.close()
    
    return {"success": True, "assignment": assignment}


if __name__ == '__main__':
    # Render 会自动设置 PORT 环境变量，如果没有则使用默认值 8001
    port = int(os.getenv('PORT', 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

