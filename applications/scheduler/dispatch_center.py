#!/usr/bin/env python3
"""
Dispatch指挥中心
Real-time监控和IntelligentDispatch决策
"""

import json
import time
from typing import Dict, List, Any
from confluent_kafka import Consumer, Producer
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from collections import defaultdict
import asyncio

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')

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
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'dispatch-center',
        'auto.offset.reset': 'earliest'  # 从最早的消息开始读取，确保不遗漏数据
    })
    
    topics = [
        'orders',
        'vehicle_locations',
        'warehouse_inventory_levels',
        'demand_predictions',
        'anomaly_alerts',
        'warehouse_pressure_alerts'
    ]
    
    consumer.subscribe(topics)
    
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'dispatch-center'
    })
    
    print("Dispatch中心Kafka消费者AlreadyStart")
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            if msg.error():
                continue
            
            topic = msg.topic()
            
            try:
                data = json.loads(msg.value().decode('utf-8'))
                
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
                    producer.produce(
                        'dispatch_assignments',
                        key=order_id.encode('utf-8'),
                        value=json.dumps(assignment).encode('utf-8')
                    )
                    producer.poll(0)
                    
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
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        producer.flush()


# Start后台Kafka消费者
import threading
consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
consumer_thread.start()


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
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'dispatch-center'
    })
    
    producer.produce(
        'dispatch_assignments',
        key=order_id.encode('utf-8'),
        value=json.dumps(assignment).encode('utf-8')
    )
    producer.flush()
    
    return {"success": True, "assignment": assignment}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8001)

