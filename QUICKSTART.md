# 快速开始指南

## 5分钟快速体验

### 1. 环境准备

确保已安装：
- Docker & Docker Compose
- Python 3.9+
- Node.js 16+

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，至少配置Kafka连接信息
```

### 3. 一键启动

```bash
# 安装Python依赖
pip install -r requirements.txt

# 启动所有服务
./deployment/deploy.sh
```

### 4. 访问仪表板

打开浏览器访问: http://localhost:3000

## 功能演示

### 查看实时订单

```bash
# 查看订单流
docker exec -it deployment-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning
```

### 查看车辆位置

```bash
# 查看车辆位置流
docker exec -it deployment-kafka-1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic vehicle_locations \
  --from-beginning
```

### 测试API

```bash
# 获取调度中心状态
curl http://localhost:8001/api/v1/status

# 获取统计信息
curl http://localhost:8001/api/v1/statistics

# 获取告警列表
curl http://localhost:8001/api/v1/alerts
```

### 测试需求预测

```bash
curl -X POST http://localhost:8000/api/v1/predict/demand \
  -H "Content-Type: application/json" \
  -d '{
    "city": "北京",
    "region": "NORTH",
    "hour_of_day": 14,
    "day_of_week": 1,
    "historical_orders": []
  }'
```

### 测试异常检测

```bash
curl -X POST http://localhost:8000/api/v1/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "vehicle",
    "features": {
      "fuel_level": 10,
      "speed_kmh": 5,
      "status": "IN_TRANSIT",
      "capacity_ratio": 0.8
    }
  }'
```

## 常见问题

### Q: Kafka连接失败？

A: 检查Docker服务是否运行：
```bash
docker ps | grep kafka
docker logs deployment-kafka-1
```

### Q: 服务启动失败？

A: 检查端口占用：
```bash
lsof -i :8000
lsof -i :8001
lsof -i :9092
```

### Q: 数据没有显示？

A: 确保数据模拟器正在运行，检查Kafka topics：
```bash
docker exec -it deployment-kafka-1 kafka-topics --list --bootstrap-server localhost:9092
```

## 下一步

- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解系统架构
- 阅读 [DEPLOYMENT.md](DEPLOYMENT.md) 了解详细部署步骤
- 查看代码了解实现细节

