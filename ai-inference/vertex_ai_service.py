#!/usr/bin/env python3
"""
Vertex AI Model Service
Provides demand prediction, warehouse pressure prediction, ETA updates, and anomaly detection
"""

import os
import json
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip
import pandas as pd
import numpy as np
from confluent_kafka import Consumer, Producer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# Configuration
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
ENDPOINT_ID = os.getenv('VERTEX_AI_ENDPOINT_ID', '')  # Need to create endpoint first

app = FastAPI(title="Amazon Logistics AI Service")

# Initialize Vertex AI
aiplatform.init(project=PROJECT_ID, location=LOCATION)


class DemandPredictionRequest(BaseModel):
    """Demand prediction request"""
    city: str
    region: str
    hour_of_day: int
    day_of_week: int
    historical_orders: List[Dict[str, Any]]


class WarehousePressureRequest(BaseModel):
    """Warehouse pressure prediction request"""
    warehouse_id: str
    current_orders: int
    current_capacity: int
    pending_orders: int
    historical_data: List[Dict[str, Any]]


class ETAUpdateRequest(BaseModel):
    """ETA update request"""
    vehicle_id: str
    current_location: Dict[str, float]
    destination: Dict[str, float]
    current_speed: float
    traffic_conditions: Dict[str, Any]
    remaining_stops: int


class AnomalyDetectionRequest(BaseModel):
    """Anomaly detection request"""
    entity_type: str  # 'order', 'vehicle', 'warehouse'
    features: Dict[str, Any]


class DemandPredictionModel:
    """Demand prediction model (LSTM + external features)"""
    
    def __init__(self):
        self.model_name = "demand_prediction_model"
        self.endpoint = None
        if ENDPOINT_ID:
            self.endpoint = aiplatform.Endpoint(ENDPOINT_ID)
    
    def predict(self, city: str, region: str, hour: int, day: int, 
                historical: List[Dict]) -> Dict[str, Any]:
        """
        Predict demand for the next 2 hours
        
        Returns:
            {
                'predicted_orders': int,
                'confidence': float,
                'time_windows': [
                    {'window': '0-1h', 'orders': int},
                    {'window': '1-2h', 'orders': int}
                ]
            }
        """
        # Simplified implementation: statistical prediction based on historical data
        # Production environment should use trained LSTM model
        
        if not historical:
            # Default prediction (based on time and region)
            base_orders = 50
            if 8 <= hour <= 10 or 17 <= hour <= 19:
                base_orders *= 1.5  # Peak hours
            if day >= 5:
                base_orders *= 0.8  # Weekend
            
            return {
                'predicted_orders': int(base_orders),
                'confidence': 0.6,
                'time_windows': [
                    {'window': '0-1h', 'orders': int(base_orders * 0.6)},
                    {'window': '1-2h', 'orders': int(base_orders * 0.4)}
                ]
            }
        
        # Predict based on historical data
        df = pd.DataFrame(historical)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['hour'] = df['timestamp'].dt.hour
        
        # Calculate historical average for the same time period
        same_hour_avg = df[df['hour'] == hour]['order_count'].mean() if 'order_count' in df.columns else 50
        
        predicted = int(same_hour_avg * 1.1)  # Add 10% as trend
        
        return {
            'predicted_orders': predicted,
            'confidence': 0.75,
            'time_windows': [
                {'window': '0-1h', 'orders': int(predicted * 0.6)},
                {'window': '1-2h', 'orders': int(predicted * 0.4)}
            ],
            'model_type': 'statistical_baseline'
        }
    
    def predict_with_vertex_ai(self, features: List[float]) -> Dict[str, Any]:
        """Predict using Vertex AI endpoint"""
        if not self.endpoint:
            return self.predict("", "", 12, 1, [])
        
        try:
            instances = [{"features": features}]
            response = self.endpoint.predict(instances=instances)
            
            predictions = response.predictions[0]
            return {
                'predicted_orders': int(predictions.get('orders', 0)),
                'confidence': float(predictions.get('confidence', 0.5)),
                'time_windows': predictions.get('windows', [])
            }
        except Exception as e:
            print(f"Vertex AI prediction error: {e}")
            return self.predict("", "", 12, 1, [])


class WarehousePressureModel:
    """Warehouse分拣PressurePrediction模型"""
    
    def predict(self, warehouse_id: str, current_orders: int, 
                current_capacity: int, pending_orders: int,
                historical: List[Dict]) -> Dict[str, Any]:
        """
        PredictionWarehouse分拣Pressure
        
        Returns:
            {
                'pressure_level': str,  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
                'pressure_score': float,  # 0-1
                'estimated_completion_time': int,  # minutes
                'recommendations': List[str]
            }
        """
        # 计算当前Pressure
        utilization = current_orders / current_capacity if current_capacity > 0 else 0
        pending_ratio = pending_orders / current_capacity if current_capacity > 0 else 0
        
        pressure_score = (utilization * 0.6 + pending_ratio * 0.4)
        
        if pressure_score >= 0.9:
            level = 'CRITICAL'
            recommendations = ['Immediately increase sorting staff', 'Consider diverting to other warehouses', 'Pause receiving new orders']
        elif pressure_score >= 0.7:
            level = 'HIGH'
            recommendations = ['Increase sorting staff', 'Extend working hours', 'Optimize sorting process']
        elif pressure_score >= 0.5:
            level = 'MEDIUM'
            recommendations = ['Monitor sorting efficiency', 'Prepare additional resources']
        else:
            level = 'LOW'
            recommendations = ['Normal operation']
        
        # 估算完成Time（简化：基于当前Order和容量）
        estimated_minutes = int((current_orders + pending_orders) / max(current_capacity, 1) * 60)
        
        return {
            'warehouse_id': warehouse_id,
            'pressure_level': level,
            'pressure_score': round(pressure_score, 2),
            'current_utilization': round(utilization, 2),
            'pending_orders': pending_orders,
            'estimated_completion_time_minutes': estimated_minutes,
            'recommendations': recommendations,
            'timestamp': int(time.time() * 1000)
        }


class ETADynamicUpdateModel:
    """ETA动态Update模型"""
    
    def calculate_eta(self, current_location: Dict[str, float],
                     destination: Dict[str, float], current_speed: float,
                     traffic_conditions: Dict[str, Any], 
                     remaining_stops: int) -> Dict[str, Any]:
        """
        动态计算ETA
        
        Returns:
            {
                'eta_minutes': int,
                'eta_timestamp': int,
                'distance_km': float,
                'estimated_speed_kmh': float,
                'confidence': float
            }
        """
        from math import radians, cos, sin, asin, sqrt
        
        # 计算距离
        lat1, lon1 = current_location['latitude'], current_location['longitude']
        lat2, lon2 = destination['latitude'], destination['longitude']
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance_km = 6371 * c
        
        # 根据交通条件调整Speed
        base_speed = current_speed
        congestion = traffic_conditions.get('congestion_percentage', 0)
        
        # Speed调整：拥堵时减速
        if congestion > 70:
            adjusted_speed = base_speed * 0.4
        elif congestion > 40:
            adjusted_speed = base_speed * 0.6
        else:
            adjusted_speed = base_speed * 0.9
        
        # 考虑剩余停靠点（每个停靠点平均5minutes）
        stop_time_minutes = remaining_stops * 5
        
        # 计算行驶Time
        if adjusted_speed > 0:
            travel_time_minutes = (distance_km / adjusted_speed) * 60
        else:
            travel_time_minutes = distance_km * 2  # 默认30km/h
        
        total_eta_minutes = int(travel_time_minutes + stop_time_minutes)
        
        return {
            'eta_minutes': total_eta_minutes,
            'eta_timestamp': int((time.time() + total_eta_minutes * 60) * 1000),
            'distance_km': round(distance_km, 2),
            'estimated_speed_kmh': round(adjusted_speed, 2),
            'base_speed_kmh': round(base_speed, 2),
            'congestion_impact': round(congestion, 2),
            'remaining_stops': remaining_stops,
            'confidence': 0.8 if congestion < 50 else 0.6,
            'timestamp': int(time.time() * 1000)
        }


class AnomalyDetectionModel:
    """Anomaly检测模型"""
    
    def detect(self, entity_type: str, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测Anomaly
        
        Returns:
            {
                'is_anomaly': bool,
                'anomaly_score': float,
                'anomaly_type': str,
                'severity': str,  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
                'description': str
            }
        """
        is_anomaly = False
        anomaly_score = 0.0
        anomaly_type = None
        severity = 'LOW'
        description = ''
        
        if entity_type == 'order':
            # OrderAnomaly检测
            item_count = features.get('item_count', 0)
            total_weight = features.get('total_weight', 0)
            
            if item_count > 20:
                is_anomaly = True
                anomaly_score = 0.8
                anomaly_type = 'LARGE_ORDER'
                severity = 'MEDIUM'
                description = f'Order item count anomaly: {item_count} items'
            
            if total_weight > 50:
                is_anomaly = True
                anomaly_score = max(anomaly_score, 0.7)
                anomaly_type = 'HEAVY_ORDER'
                severity = 'MEDIUM'
                description = f'Order weight anomaly: {total_weight}kg'
        
        elif entity_type == 'vehicle':
            # VehicleAnomaly检测
            fuel_level = features.get('fuel_level', 100)
            speed = features.get('speed_kmh', 0)
            status = features.get('status', '')
            capacity_ratio = features.get('capacity_ratio', 0)
            
            if fuel_level < 15:
                is_anomaly = True
                anomaly_score = 0.9
                anomaly_type = 'LOW_FUEL'
                severity = 'HIGH'
                description = f'Low fuel: {fuel_level}%'
            
            if status == 'IN_TRANSIT' and speed < 5 and fuel_level > 50:
                is_anomaly = True
                anomaly_score = max(anomaly_score, 0.6)
                anomaly_type = 'LOW_SPEED'
                severity = 'MEDIUM'
                description = 'Vehicle low speed anomaly, possible issue'
            
            if capacity_ratio > 1.0:
                is_anomaly = True
                anomaly_score = 0.95
                anomaly_type = 'OVERLOADED'
                severity = 'CRITICAL'
                description = 'Vehicle overloaded'
        
        elif entity_type == 'warehouse':
            # WarehouseAnomaly检测
            utilization = features.get('utilization', 0)
            pending_orders = features.get('pending_orders', 0)
            
            if utilization > 0.95:
                is_anomaly = True
                anomaly_score = 0.9
                anomaly_type = 'HIGH_UTILIZATION'
                severity = 'HIGH'
                description = f'Warehouse utilization too high: {utilization*100:.1f}%'
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': round(anomaly_score, 2),
            'anomaly_type': anomaly_type,
            'severity': severity,
            'description': description,
            'entity_type': entity_type,
            'timestamp': int(time.time() * 1000)
        }


# Initialize模型
demand_model = DemandPredictionModel()
pressure_model = WarehousePressureModel()
eta_model = ETADynamicUpdateModel()
anomaly_model = AnomalyDetectionModel()


# API端点
@app.post("/api/v1/predict/demand")
async def predict_demand(request: DemandPredictionRequest):
    """DemandPredictionAPI"""
    try:
        result = demand_model.predict(
            request.city,
            request.region,
            request.hour_of_day,
            request.day_of_week,
            request.historical_orders
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/predict/warehouse-pressure")
async def predict_warehouse_pressure(request: WarehousePressureRequest):
    """WarehousePressurePredictionAPI"""
    try:
        result = pressure_model.predict(
            request.warehouse_id,
            request.current_orders,
            request.current_capacity,
            request.pending_orders,
            request.historical_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/calculate/eta")
async def calculate_eta(request: ETAUpdateRequest):
    """ETA计算API"""
    try:
        result = eta_model.calculate_eta(
            request.current_location,
            request.destination,
            request.current_speed,
            request.traffic_conditions,
            request.remaining_stops
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/detect/anomaly")
async def detect_anomaly(request: AnomalyDetectionRequest):
    """Anomaly检测API"""
    try:
        result = anomaly_model.detect(request.entity_type, request.features)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "vertex-ai-service"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)

