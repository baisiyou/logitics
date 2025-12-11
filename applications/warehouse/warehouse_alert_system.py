#!/usr/bin/env python3
"""
Warehouse分拣预警System
Real-time监控WarehousePressure，Send预警通知
"""

import json
import time
from confluent_kafka import Consumer, Producer
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')

app = FastAPI(title="Warehouse Alert System")

# WarehouseAlertStatus
warehouse_alerts = defaultdict(list)  # {warehouse_id: [alerts]}


def send_alert_notification(warehouse_id: str, alert: Dict[str, Any]):
    """SendAlert通知（Email/SMS/Push）"""
    # Simplified implementation：打印日志
    # 生产环境应集成邮件Service、短信Service、企业IM等
    
    severity = alert.get('severity', 'MEDIUM')
    pressure_level = alert.get('pressure_level', 'UNKNOWN')
    recommendations = alert.get('recommendations', [])
    
    message = f"""
Warehouse Alert Notification
============================
Warehouse ID: {warehouse_id}
Severity: {severity}
Pressure Level: {pressure_level}
Pressure Score: {alert.get('pressure_score', 0)}
Current Utilization: {alert.get('current_utilization', 0) * 100:.1f}%
Pending Orders: {alert.get('pending_orders', 0)}
Estimated Completion Time: {alert.get('estimated_completion_time_minutes', 0)} minutes

Recommendations:
{chr(10).join(f'- {rec}' for rec in recommendations)}

Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.get('timestamp', time.time()) / 1000))}
"""
    
    print(f"\n{'='*50}")
    print(message)
    print(f"{'='*50}\n")
    
    # 生产环境实现：
    # 1. Send邮件
    # 2. Send短信（高严重度）
    # 3. 推送到企业IM（钉钉、企业微信等）
    # 4. 记录到AlertSystem


def kafka_consumer_loop():
    """Kafka consumer: listening toWarehousePressureAlert"""
    consumer = Consumer({
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': 'warehouse-alert-system',
        'auto.offset.reset': 'latest'
    })
    
    consumer.subscribe(['warehouse_pressure_alerts', 'anomaly_alerts'])
    
    print("Warehouse预警SystemAlreadyStart")
    
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
                
                if topic == 'warehouse_pressure_alerts':
                    warehouse_id = data.get('warehouse_id')
                    if warehouse_id:
                        # 存储Alert
                        warehouse_alerts[warehouse_id].append(data)
                        
                        # 只保留最近50条
                        if len(warehouse_alerts[warehouse_id]) > 50:
                            warehouse_alerts[warehouse_id] = warehouse_alerts[warehouse_id][-50:]
                        
                        # Send通知
                        send_alert_notification(warehouse_id, data)
                
                elif topic == 'anomaly_alerts':
                    # 如果是Warehouse相关Anomaly
                    entity_type = data.get('entity_type')
                    if entity_type == 'warehouse':
                        warehouse_id = data.get('warehouse_id') or data.get('entity_id')
                        if warehouse_id:
                            warehouse_alerts[warehouse_id].append(data)
                            send_alert_notification(warehouse_id, data)
                
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


@app.get("/api/v1/alerts/{warehouse_id}")
async def get_warehouse_alerts(warehouse_id: str, limit: int = 20):
    """获取WarehouseAlert列表"""
    alerts = warehouse_alerts.get(warehouse_id, [])
    return {
        "warehouse_id": warehouse_id,
        "alerts": alerts[-limit:],
        "total_count": len(alerts)
    }


@app.get("/api/v1/alerts")
async def get_all_alerts(limit: int = 50):
    """获取所有WarehouseAlert"""
    all_alerts = []
    for warehouse_id, alerts in warehouse_alerts.items():
        for alert in alerts:
            alert['warehouse_id'] = warehouse_id
            all_alerts.append(alert)
    
    # 按Time排序
    all_alerts.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    return {
        "alerts": all_alerts[:limit],
        "total_count": len(all_alerts)
    }


@app.get("/api/v1/warehouses/{warehouse_id}/status")
async def get_warehouse_status(warehouse_id: str):
    """获取WarehouseCurrent Status"""
    alerts = warehouse_alerts.get(warehouse_id, [])
    
    if not alerts:
        return {
            "warehouse_id": warehouse_id,
            "status": "NORMAL",
            "latest_alert": None
        }
    
    latest_alert = alerts[-1]
    pressure_level = latest_alert.get('pressure_level', 'LOW')
    
    return {
        "warehouse_id": warehouse_id,
        "status": pressure_level,
        "latest_alert": latest_alert,
        "alert_count_24h": len([a for a in alerts 
                               if time.time() * 1000 - a.get('timestamp', 0) < 86400000])
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "warehouse-alert-system"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8003)

