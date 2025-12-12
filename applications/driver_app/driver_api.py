#!/usr/bin/env python3
"""
DriverAPP API
提供Driver端Real-time推送和任务管理
"""

import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from confluent_kafka import Consumer, Producer
import uvicorn
import os
from dotenv import load_dotenv
from collections import defaultdict
import asyncio

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')

app = FastAPI(title="Driver App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DriverState storage
driver_state = defaultdict(dict)  # {driver_id: {assignments, location, status}}


class TaskAssignment(BaseModel):
    """任务分配"""
    assignment_id: str
    order_id: str
    pickup_location: Dict[str, Any]
    delivery_location: Dict[str, Any]
    priority: str
    estimated_pickup_time: int
    estimated_delivery_time: int
    items: List[Dict[str, Any]]


class LocationUpdate(BaseModel):
    """位置Update"""
    driver_id: str
    latitude: float
    longitude: float
    timestamp: int


class TaskStatusUpdate(BaseModel):
    """Task statusUpdate"""
    assignment_id: str
    status: str  # 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'FAILED'
    timestamp: int
    notes: str = ""


# WebSocket connection management（按DriverID）
class DriverConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, driver_id: str):
        await websocket.accept()
        self.connections[driver_id] = websocket
    
    def disconnect(self, driver_id: str):
        if driver_id in self.connections:
            del self.connections[driver_id]
    
    async def send_to_driver(self, driver_id: str, message: dict):
        if driver_id in self.connections:
            try:
                await self.connections[driver_id].send_json(message)
                return True
            except:
                self.disconnect(driver_id)
                return False
        return False
    
    async def broadcast(self, message: dict):
        for driver_id, websocket in list(self.connections.items()):
            try:
                await websocket.send_json(message)
            except:
                self.disconnect(driver_id)

manager = DriverConnectionManager()


def kafka_consumer_loop():
    """Kafka consumer: listening toDispatch指令和ETAUpdate"""
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'driver-app',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['dispatch_assignments', 'eta_updates', 'anomaly_alerts'])
    
    print("DriverAPP Kafka消费者AlreadyStart")
    
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
                
                if topic == 'dispatch_assignments':
                    # 获取VehicleID，找到对应的Driver
                    vehicle_id = data.get('assigned_vehicle')
                    if vehicle_id:
                        # 简化：从VehicleData获取DriverID
                        # 实际应从vehicle_locations流获取
                        driver_id = f"DRV{vehicle_id[-4:]}"  # Simplified mapping
                        
                        # Send任务分配通知
                        asyncio.create_task(manager.send_to_driver(driver_id, {
                            'type': 'new_assignment',
                            'data': data
                        }))
                        
                        # UpdateDriverStatus
                        if driver_id not in driver_state:
                            driver_state[driver_id] = {'assignments': []}
                        driver_state[driver_id]['assignments'].append(data)
                
                elif topic == 'eta_updates':
                    vehicle_id = data.get('vehicle_id')
                    if vehicle_id:
                        driver_id = f"DRV{vehicle_id[-4:]}"
                        
                        # SendETAUpdate
                        asyncio.create_task(manager.send_to_driver(driver_id, {
                            'type': 'eta_update',
                            'data': data
                        }))
                
                elif topic == 'anomaly_alerts':
                    # 如果是Vehicle相关Alert，Send给对应Driver
                    vehicle_id = data.get('vehicle_id')
                    if vehicle_id:
                        driver_id = f"DRV{vehicle_id[-4:]}"
                        
                        asyncio.create_task(manager.send_to_driver(driver_id, {
                            'type': 'alert',
                            'data': data
                        }))
                
            except Exception as e:
                print(f"ProcessError: {e}")
                
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


# Start后台消费者
import threading
consumer_thread = threading.Thread(target=kafka_consumer_loop, daemon=True)
consumer_thread.start()


@app.websocket("/ws/{driver_id}")
async def driver_websocket(websocket: WebSocket, driver_id: str):
    """DriverWebSocket连接"""
    await manager.connect(websocket, driver_id)
    
    # SendCurrent Status
    current_state = driver_state.get(driver_id, {})
    await websocket.send_json({
        'type': 'initial_state',
        'data': current_state
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # ProcessDriverSend的Message
            msg_type = data.get('type')
            
            if msg_type == 'location_update':
                # Update位置
                location = data.get('data', {})
                if driver_id in driver_state:
                    driver_state[driver_id]['location'] = location
                    driver_state[driver_id]['last_update'] = int(time.time() * 1000)
            
            elif msg_type == 'task_status':
                # UpdateTask status
                status_data = data.get('data', {})
                assignment_id = status_data.get('assignment_id')
                
                if driver_id in driver_state:
                    assignments = driver_state[driver_id].get('assignments', [])
                    for assignment in assignments:
                        if assignment.get('order_id') == assignment_id:
                            assignment['status'] = status_data.get('status')
                            assignment['status_timestamp'] = status_data.get('timestamp')
                            break
            
    except WebSocketDisconnect:
        manager.disconnect(driver_id)


@app.get("/api/v1/driver/{driver_id}/assignments")
async def get_assignments(driver_id: str):
    """获取Driver的任务列表"""
    if driver_id not in driver_state:
        return {"assignments": []}
    
    return {
        "driver_id": driver_id,
        "assignments": driver_state[driver_id].get('assignments', []),
        "current_location": driver_state[driver_id].get('location')
    }


@app.post("/api/v1/driver/{driver_id}/location")
async def update_location(driver_id: str, location: LocationUpdate):
    """UpdateDriver位置"""
    if driver_id not in driver_state:
        driver_state[driver_id] = {}
    
    driver_state[driver_id]['location'] = {
        'latitude': location.latitude,
        'longitude': location.longitude,
        'timestamp': location.timestamp
    }
    
    # Send位置Update到Kafka
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'driver-app'
    })
    
    producer.produce(
        'vehicle_locations',
        key=driver_id.encode('utf-8'),
        value=json.dumps({
            'driver_id': driver_id,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'timestamp': location.timestamp
        }).encode('utf-8')
    )
    producer.flush()
    
    return {"success": True}


@app.post("/api/v1/driver/{driver_id}/task-status")
async def update_task_status(driver_id: str, status: TaskStatusUpdate):
    """UpdateTask status"""
    if driver_id not in driver_state:
        raise HTTPException(status_code=404, detail="Driver不存在")
    
    # UpdateTask status
    assignments = driver_state[driver_id].get('assignments', [])
    updated = False
    
    for assignment in assignments:
        if assignment.get('order_id') == status.assignment_id:
            assignment['status'] = status.status
            assignment['status_timestamp'] = status.timestamp
            assignment['notes'] = status.notes
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Task does not exist")
    
    # SendStatusUpdate到Kafka
    producer = Producer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'driver-app'
    })
    
    producer.produce(
        'task_status_updates',
        key=status.assignment_id.encode('utf-8'),
        value=json.dumps({
            'driver_id': driver_id,
            'assignment_id': status.assignment_id,
            'status': status.status,
            'timestamp': status.timestamp,
            'notes': status.notes
        }).encode('utf-8')
    )
    producer.flush()
    
    return {"success": True}


@app.get("/api/v1/driver/{driver_id}/eta")
async def get_eta(driver_id: str):
    """获取Driver的ETA信息"""
    # 从Kafka读取最新的ETAUpdate
    # Simplified implementation
    return {
        "driver_id": driver_id,
        "eta_updates": []
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "driver-app"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8002)

