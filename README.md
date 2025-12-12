# Amazon Logistics Network Real-Time Intelligent Dispatch System

A real-time intelligent dispatch system based on Confluent data streaming and Google Cloud AI, enabling dynamic optimization and matching of warehouses, vehicles, and packages.

## 🎯 Core Features

1. **Real-Time Demand Forecasting**: Predict order volumes for each region 2 hours in advance
2. **Dynamic Inventory Allocation**: Intelligent stock transfer between warehouses
3. **Intelligent Route Planning**: Real-time traffic-aware delivery routes
4. **Anomaly Alert System**: Early warning for delivery delay risks

## 🏗️ System Architecture

```
[Data Source Layer] → [Confluent Processing Layer] → [AI Inference Layer] → [Application Layer]
```

For detailed architecture documentation, please refer to [ARCHITECTURE.md](ARCHITECTURE.md)

## 📁 Project Structure

```
amazon/
├── data-sources/          # Data Source Layer
│   ├── kafka_topics.json  # Kafka Topics Configuration
│   ├── schemas/          # Avro Data Schemas
│   └── simulators/       # Data Simulators
├── confluent/            # Confluent Processing Layer
│   ├── ksqldb/          # ksqlDB Queries
│   └── stream_processors/ # Stream Processors
├── ai-inference/         # AI Inference Layer
│   ├── vertex_ai_service.py    # Vertex AI Service
│   ├── kafka_ai_processor.py   # Kafka AI Processor
│   └── bigquery_ml_queries.sql # BigQuery ML Queries
├── applications/         # Application Layer
│   ├── scheduler/        # Dispatch Center
│   ├── driver_app/      # Driver App API
│   ├── warehouse/       # Warehouse Alert System
│   ├── customer/        # Customer ETA Service
│   └── dashboard/       # Frontend Dashboard
├── deployment/          # Deployment Scripts
│   ├── docker-compose.yml
│   ├── deploy.sh
│   └── stop.sh
└── scripts/             # Utility Scripts
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Node.js 16+
- Google Cloud Platform account (optional, for AI features)
- Confluent Cloud account or local Kafka cluster

### One-Click Deployment

```bash
# 1. Clone the project
cd /Users/zrb/Documents/amazon

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file, at minimum configure Kafka connection information

# 4. One-click deployment
./deployment/deploy.sh
```

For detailed deployment steps, please refer to [DEPLOYMENT.md](DEPLOYMENT.md)  
For a quick experience, please refer to [QUICKSTART.md](QUICKSTART.md)

### Access Services

- **Dispatch Center Dashboard**: http://localhost:8001
- **Driver App API**: http://localhost:8002
- **Warehouse Alert System**: http://localhost:8003
- **Customer ETA Service**: http://localhost:8004
- **AI Inference Service**: http://localhost:8000
- **Frontend Dashboard**: http://localhost:3000

## 🛠️ Technology Stack

### Data Streaming
- **Kafka**: Message queue and event streaming
- **ksqlDB**: Stream SQL queries
- **Schema Registry**: Data schema management

### AI/ML
- **Vertex AI**: Model training and deployment
- **BigQuery ML**: Real-time ML queries
- **TensorFlow**: Deep learning models

### Backend Services
- **FastAPI**: Python web framework
- **WebSocket**: Real-time communication
- **PostgreSQL**: Relational database
- **Redis**: Cache and state storage

### Frontend
- **React**: UI framework
- **Material-UI**: Component library
- **Leaflet**: Map component
- **Recharts**: Chart library

## 📊 Data Flow

### Order Processing Flow
```
Order Creation → orders topic → Order Enrichment → Demand Prediction → Dispatch Optimization → Vehicle Assignment
```

### Vehicle Tracking Flow
```
Vehicle GPS → vehicle_locations → Traffic Association → ETA Calculation → Customer Notification
```

### Warehouse Monitoring Flow
```
Inventory Update → inventory_updates → Real-time Aggregation → Pressure Prediction → Alert Notification
```

## 🔧 Development Guide

### Running Data Simulators

```bash
# Order simulator
python data-sources/simulators/order_simulator.py

# Vehicle location simulator
python data-sources/simulators/vehicle_location_simulator.py

# Inventory simulator
python data-sources/simulators/inventory_simulator.py
```

### Testing APIs

```bash
# Demand prediction
curl -X POST http://localhost:8000/api/v1/predict/demand \
  -H "Content-Type: application/json" \
  -d '{"city": "Montreal", "region": "NORTH", "hour_of_day": 14, "day_of_week": 1, "historical_orders": []}'

# Anomaly detection
curl -X POST http://localhost:8000/api/v1/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "vehicle", "features": {"fuel_level": 10, "speed_kmh": 5}}'
```

## 📚 Documentation

- [System Architecture](ARCHITECTURE.md) - Detailed system architecture documentation
- [Deployment Guide](DEPLOYMENT.md) - Complete deployment steps
- [Quick Start Guide](QUICKSTART.md) - 5-minute quick experience

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📄 License

MIT License
