# 部署指南

## 系统架构

本系统采用微服务架构，包含以下组件：

1. **数据源层**: Kafka Topics + 数据模拟器
2. **Confluent处理层**: ksqlDB + 流处理器
3. **AI推理层**: Vertex AI服务 + BigQuery ML
4. **应用层**: 调度中心、司机APP、仓库预警、客户ETA服务

## 前置要求

### 1. 软件依赖

- Docker & Docker Compose
- Python 3.9+
- Node.js 16+
- Google Cloud SDK (用于Vertex AI)
- Confluent Cloud账号 或 本地Kafka集群

### 2. 服务账号配置

#### Google Cloud配置

1. 创建GCP项目
2. 启用以下API：
   - Vertex AI API
   - BigQuery API
   - Cloud Storage API

3. 创建服务账号并下载密钥：
```bash
gcloud iam service-accounts create logistics-ai-service
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:logistics-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
gcloud iam service-accounts keys create service-account.json \
    --iam-account=logistics-ai-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

4. 设置环境变量：
```bash
export GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
```

#### Confluent Cloud配置

1. 登录Confluent Cloud控制台
2. 创建集群和环境
3. 创建API密钥
4. 在`.env`文件中配置：
```
CONFLUENT_BOOTSTRAP_SERVERS=your-bootstrap-servers
CONFLUENT_API_KEY=your-api-key
CONFLUENT_API_SECRET=your-api-secret
CONFLUENT_SCHEMA_REGISTRY_URL=your-schema-registry-url
```

## 部署步骤

### 1. 克隆和配置

```bash
cd /Users/zrb/Documents/amazon
cp .env.example .env
# 编辑 .env 文件，填写所有配置
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 启动基础设施

```bash
cd deployment
docker-compose up -d
```

等待所有服务启动（约30秒）：
```bash
docker-compose ps
```

### 4. 创建Kafka Topics

```bash
# 使用Confluent CLI或Python脚本创建topics
python3 scripts/create_topics.py
```

### 5. 初始化ksqlDB

```bash
# 连接到ksqlDB CLI
docker exec -it deployment-ksqldb-cli-1 ksql http://ksqldb-server:8088

# 执行查询文件
RUN SCRIPT '../confluent/ksqldb/queries.sql';
```

### 6. 启动数据源模拟器

```bash
# 终端1: 订单模拟器
python3 data-sources/simulators/order_simulator.py

# 终端2: 车辆位置模拟器
python3 data-sources/simulators/vehicle_location_simulator.py

# 终端3: 库存模拟器
python3 data-sources/simulators/inventory_simulator.py
```

### 7. 启动流处理器

```bash
# 终端4: 订单富化器
python3 confluent/stream_processors/order_enricher.py

# 终端5: 流关联器
python3 confluent/stream_processors/stream_joiner.py
```

### 8. 启动AI服务

```bash
# 终端6: Vertex AI服务
python3 ai-inference/vertex_ai_service.py

# 终端7: Kafka AI处理器
python3 ai-inference/kafka_ai_processor.py
```

### 9. 启动应用层服务

```bash
# 终端8: 调度中心
python3 applications/scheduler/dispatch_center.py

# 终端9: 司机APP API
python3 applications/driver_app/driver_api.py

# 终端10: 仓库预警系统
python3 applications/warehouse/warehouse_alert_system.py

# 终端11: 客户ETA服务
python3 applications/customer/customer_eta_service.py
```

### 10. 启动前端仪表板

```bash
cd applications/dashboard
npm install
npm start
```

## 使用自动化部署脚本

```bash
# 一键部署
chmod +x deployment/deploy.sh
./deployment/deploy.sh

# 停止所有服务
chmod +x deployment/stop.sh
./deployment/stop.sh
```

## 验证部署

### 1. 检查Kafka Topics

```bash
docker exec -it deployment-kafka-1 kafka-topics --list --bootstrap-server localhost:9092
```

### 2. 检查服务健康

- 调度中心: http://localhost:8001/health
- 司机APP: http://localhost:8002/health
- 仓库预警: http://localhost:8003/health
- 客户ETA: http://localhost:8004/health
- AI服务: http://localhost:8000/health

### 3. 查看仪表板

打开浏览器访问: http://localhost:3000

## 生产环境部署建议

### 1. 使用Kubernetes

- 将所有服务容器化
- 使用Kubernetes部署和管理
- 配置自动扩缩容

### 2. 监控和日志

- 集成Prometheus + Grafana
- 使用ELK Stack收集日志
- 设置告警规则

### 3. 高可用性

- Kafka集群多副本
- 服务多实例部署
- 数据库主从复制

### 4. 安全

- 使用TLS加密Kafka连接
- API认证和授权
- 密钥管理（Vault/Secrets Manager）

## 故障排查

### Kafka连接问题

```bash
# 检查Kafka是否运行
docker ps | grep kafka

# 查看Kafka日志
docker logs deployment-kafka-1
```

### 服务启动失败

1. 检查端口是否被占用
2. 检查环境变量配置
3. 查看服务日志

### AI服务错误

1. 验证GCP服务账号权限
2. 检查Vertex AI API是否启用
3. 验证项目ID和区域配置

## 性能优化

1. **Kafka优化**
   - 调整分区数量
   - 优化批处理大小
   - 配置压缩

2. **AI推理优化**
   - 使用模型缓存
   - 批量预测
   - 异步处理

3. **数据库优化**
   - 索引优化
   - 连接池配置
   - 查询优化

## 扩展功能

- 集成更多数据源（天气API、交通API）
- 添加更多AI模型
- 实现更复杂的调度算法
- 添加移动端应用

