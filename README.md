# 亚马逊物流网络实时智能调度系统

基于Confluent数据流和Google Cloud AI的实时智能调度系统，实现仓库、车辆、包裹的动态优化匹配。

## 🎯 核心功能

1. **实时需求预测**：提前2小时预测各区域订单量
2. **动态库存调配**：仓库间智能调拨
3. **智能路径规划**：实时交通感知的配送路线
4. **异常预警系统**：延误风险提前预警

## 🏗️ 系统架构

```
[数据源层] → [Confluent处理层] → [AI推理层] → [应用层]
```

详细架构说明请参考 [ARCHITECTURE.md](ARCHITECTURE.md)

## 📁 项目结构

```
amazon/
├── data-sources/          # 数据源层
│   ├── kafka_topics.json  # Kafka Topics配置
│   ├── schemas/          # Avro数据模式
│   └── simulators/       # 数据模拟器
├── confluent/            # Confluent处理层
│   ├── ksqldb/          # ksqlDB查询
│   └── stream_processors/ # 流处理器
├── ai-inference/         # AI推理层
│   ├── vertex_ai_service.py    # Vertex AI服务
│   ├── kafka_ai_processor.py   # Kafka AI处理器
│   └── bigquery_ml_queries.sql # BigQuery ML查询
├── applications/         # 应用层
│   ├── scheduler/        # 调度指挥中心
│   ├── driver_app/      # 司机APP API
│   ├── warehouse/       # 仓库预警系统
│   ├── customer/        # 客户ETA服务
│   └── dashboard/       # 前端仪表板
├── deployment/          # 部署脚本
│   ├── docker-compose.yml
│   ├── deploy.sh
│   └── stop.sh
└── scripts/             # 工具脚本
```

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose
- Python 3.9+
- Node.js 16+
- Google Cloud Platform账号（可选，用于AI功能）
- Confluent Cloud账号或本地Kafka集群

### 一键启动

```bash
# 1. 克隆项目
cd /Users/zrb/Documents/amazon

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少配置Kafka连接信息

# 4. 一键部署
./deployment/deploy.sh
```

详细部署步骤请参考 [DEPLOYMENT.md](DEPLOYMENT.md)  
快速体验请参考 [QUICKSTART.md](QUICKSTART.md)

### 访问服务

- **调度中心仪表板**: http://localhost:8001
- **司机APP API**: http://localhost:8002
- **仓库预警系统**: http://localhost:8003
- **客户ETA服务**: http://localhost:8004
- **AI推理服务**: http://localhost:8000
- **前端仪表板**: http://localhost:3000

## 🛠️ 技术栈

### 数据流处理
- **Kafka**: 消息队列和事件流
- **ksqlDB**: 流式SQL查询
- **Schema Registry**: 数据模式管理

### AI/ML
- **Vertex AI**: 模型训练和部署
- **BigQuery ML**: 实时ML查询
- **TensorFlow**: 深度学习模型

### 后端服务
- **FastAPI**: Python Web框架
- **WebSocket**: 实时通信
- **PostgreSQL**: 关系数据库
- **Redis**: 缓存和状态存储

### 前端
- **React**: UI框架
- **Material-UI**: 组件库
- **Leaflet**: 地图组件
- **Recharts**: 图表库

## 📊 数据流

### 订单处理流程
```
订单创建 → orders topic → 订单富化 → 需求预测 → 调度优化 → 车辆分配
```

### 车辆跟踪流程
```
车辆GPS → vehicle_locations → 交通关联 → ETA计算 → 客户通知
```

### 仓库监控流程
```
库存更新 → inventory_updates → 实时聚合 → 压力预测 → 预警通知
```

## 🔧 开发指南

### 运行数据模拟器

```bash
# 订单模拟器
python data-sources/simulators/order_simulator.py

# 车辆位置模拟器
python data-sources/simulators/vehicle_location_simulator.py

# 库存模拟器
python data-sources/simulators/inventory_simulator.py
```

### 测试API

```bash
# 需求预测
curl -X POST http://localhost:8000/api/v1/predict/demand \
  -H "Content-Type: application/json" \
  -d '{"city": "北京", "region": "NORTH", "hour_of_day": 14, "day_of_week": 1, "historical_orders": []}'

# 异常检测
curl -X POST http://localhost:8000/api/v1/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "vehicle", "features": {"fuel_level": 10, "speed_kmh": 5}}'
```

## 📚 文档

- [系统架构文档](ARCHITECTURE.md) - 详细的系统架构说明
- [部署指南](DEPLOYMENT.md) - 完整的部署步骤
- [快速开始](QUICKSTART.md) - 5分钟快速体验

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

