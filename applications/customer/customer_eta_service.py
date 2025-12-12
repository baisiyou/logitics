#!/usr/bin/env python3
"""
CustomerETAReal-timeUpdateService
为Customer提供Real-timeDeliveryStatus和ETAUpdate
"""

import json
import time
from confluent_kafka import Consumer, Producer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')

app = FastAPI(title="Customer ETA Service")

# OrderETAStatus
order_etas = {}  # {order_id: eta_info}


class ETAQuery(BaseModel):
    """ETA查询请求"""
    order_id: str
    customer_id: Optional[str] = None


def kafka_consumer_loop():
    """Kafka consumer: listening toETAUpdate和Task status"""
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'customer-eta-service',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['eta_updates', 'task_status_updates', 'dispatch_assignments'])
    
    print("CustomerETAServiceAlreadyStart")
    
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
                
                if topic == 'eta_updates':
                    # ETAUpdate（需要关联到Order）
                    # 简化：从vehicle_id关联到Order
                    vehicle_id = data.get('vehicle_id')
                    # 实际应从dispatch_assignments获取Order关联
                
                elif topic == 'task_status_updates':
                    # Task statusUpdate
                    assignment_id = data.get('assignment_id')
                    status = data.get('status')
                    
                    # UpdateOrderStatus
                    # Simplified: assume assignment_id is order_id
                    order_id = assignment_id
                    if order_id not in order_etas:
                        order_etas[order_id] = {}
                    
                    order_etas[order_id]['status'] = status
                    order_etas[order_id]['status_timestamp'] = data.get('timestamp')
                    order_etas[order_id]['last_update'] = int(time.time() * 1000)
                
                elif topic == 'dispatch_assignments':
                    # Dispatch分配
                    order_id = data.get('order_id')
                    if order_id:
                        order_etas[order_id] = {
                            'order_id': order_id,
                            'assigned_vehicle': data.get('assigned_vehicle'),
                            'assigned_warehouse': data.get('assigned_warehouse'),
                            'estimated_pickup_time': data.get('estimated_pickup_time'),
                            'estimated_delivery_time': data.get('estimated_delivery_time'),
                            'status': 'ASSIGNED',
                            'last_update': int(time.time() * 1000)
                        }
                
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


@app.get("/api/v1/eta/{order_id}")
async def get_eta(order_id: str):
    """获取OrderETA"""
    if order_id not in order_etas:
        raise HTTPException(status_code=404, detail="Order不存在或尚未分配")
    
    eta_info = order_etas[order_id].copy()
    
    # 计算剩余Time
    estimated_delivery_time = eta_info.get('estimated_delivery_time')
    if estimated_delivery_time:
        current_time = int(time.time() * 1000)
        remaining_ms = estimated_delivery_time - current_time
        remaining_minutes = max(0, remaining_ms // 60000)
        
        eta_info['remaining_minutes'] = remaining_minutes
        eta_info['is_delayed'] = remaining_ms < -300000  # 延迟超过5minutes
    
    return eta_info


@app.get("/api/v1/order/{order_id}/status")
async def get_order_status(order_id: str):
    """获取OrderStatus"""
    if order_id not in order_etas:
        return {
            "order_id": order_id,
            "status": "PENDING",
            "message": "OrderAlreadyReceive，等待分配"
        }
    
    eta_info = order_etas[order_id]
    status = eta_info.get('status', 'UNKNOWN')
    
    status_messages = {
        'ASSIGNED': 'OrderAlready分配，等待取货',
        'PICKED_UP': 'OrderAlready取货，In progressDelivery中',
        'IN_TRANSIT': 'OrderIn Transit',
        'DELIVERED': 'OrderAlready送达',
        'FAILED': 'DeliveryFailed'
    }
    
    return {
        "order_id": order_id,
        "status": status,
        "message": status_messages.get(status, 'Unknown status'),
        "estimated_delivery_time": eta_info.get('estimated_delivery_time'),
        "last_update": eta_info.get('last_update')
    }


@app.post("/api/v1/eta/query")
async def query_eta(query: ETAQuery):
    """查询ETA（支持OrderID和CustomerID）"""
    if query.order_id:
        if query.order_id in order_etas:
            return get_eta(query.order_id)
        else:
            raise HTTPException(status_code=404, detail="Order不存在")
    
    # 如果只有customer_id，返回该Customer的所有Order
    # Simplified implementation
    return {"message": "请提供OrderID"}


@app.get("/api/v1/orders/{order_id}/tracking")
async def track_order(order_id: str):
    """Order追踪（完整信息）"""
    if order_id not in order_etas:
        raise HTTPException(status_code=404, detail="Order不存在")
    
    eta_info = order_etas[order_id]
    
    # Build tracking information
    tracking = {
        "order_id": order_id,
        "current_status": eta_info.get('status', 'UNKNOWN'),
        "assigned_vehicle": eta_info.get('assigned_vehicle'),
        "assigned_warehouse": eta_info.get('assigned_warehouse'),
        "estimated_pickup_time": eta_info.get('estimated_pickup_time'),
        "estimated_delivery_time": eta_info.get('estimated_delivery_time'),
        "last_update": eta_info.get('last_update')
    }
    
    # 计算Time线
    current_time = int(time.time() * 1000)
    estimated_delivery = eta_info.get('estimated_delivery_time', 0)
    
    if estimated_delivery:
        remaining_ms = estimated_delivery - current_time
        tracking['remaining_time'] = {
            'minutes': max(0, remaining_ms // 60000),
            'hours': max(0, remaining_ms // 3600000)
        }
    
    return tracking


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "customer-eta-service"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8004)

