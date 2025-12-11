# 切换到本地 Kafka 指南

## 已完成

✅ **本地 Kafka 服务已启动**
- Zookeeper: 运行中
- Kafka: 运行中
- Schema Registry: 运行中

✅ **Topics 已存在**（从验证结果看）

## 需要手动更新 .env 文件

由于 `.env` 文件受保护，请手动编辑：

### 步骤 1: 编辑 .env 文件

打开 `.env` 文件，修改以下配置：

```bash
# 将这行：
CONFLUENT_BOOTSTRAP_SERVERS=pkc-619z3.us-east1.gcp.confluent.cloud:9092

# 改为：
CONFLUENT_BOOTSTRAP_SERVERS=localhost:9092
```

```bash
# 将这行：
CONFLUENT_SCHEMA_REGISTRY_URL=https://psrc-15ov57k.us-east1.gcp.confluent.cloud

# 改为：
CONFLUENT_SCHEMA_REGISTRY_URL=http://localhost:8081
```

### 步骤 2: 注释掉 Confluent Cloud 凭证（可选）

```bash
# 在以下行前添加 # 注释：
# CONFLUENT_API_KEY=PHJD3DVVDYSYBG66
# CONFLUENT_API_SECRET=cflt/XiR5jhkfnzAdR4+LfU78gi4YW0W72zHid2EiVakkrzcuhoxHZ6cclUbG0FA
```

## 验证配置

### 1. 检查 Kafka 连接

```bash
docker exec deployment-kafka-1 kafka-topics --list --bootstrap-server localhost:9092
```

应该看到 topics 列表。

### 2. 检查 Schema Registry

```bash
curl http://localhost:8081/subjects
```

### 3. 重启服务

```bash
# 停止现有服务
./scripts/stop_services.sh

# 重新启动（会使用新的 .env 配置）
./deployment/deploy.sh
```

## 费用节省

| 项目 | 之前 | 现在 | 节省 |
|------|------|------|------|
| Confluent Cloud | ~$720-3600/月 | $0 | ~$720-3600/月 |
| 本地 Kafka | $0 | $0 | $0 |
| **总计** | **~$720-3600/月** | **$0** | **~$720-3600/月** |

## 故障排除

### Kafka 连接超时

如果遇到连接超时：

1. **等待 Kafka 完全启动**（通常需要 30-60 秒）
   ```bash
   docker logs deployment-kafka-1
   ```

2. **检查服务状态**
   ```bash
   docker ps | grep kafka
   ```

3. **重启服务**
   ```bash
   cd deployment
   docker-compose restart kafka
   ```

### Topics 创建失败

如果 topics 创建失败，Kafka 会自动创建（如果启用了 `KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'`）。

手动创建：
```bash
docker exec deployment-kafka-1 kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --partitions 3 \
  --replication-factor 1
```

## 切换回 Confluent Cloud

如果需要切换回 Confluent Cloud：

1. 恢复 `.env` 文件中的配置
2. 取消注释 Confluent Cloud 凭证
3. 重启服务

## 当前状态

✅ **本地 Kafka 运行中**
- 端口: 9092
- Schema Registry: 8081
- Zookeeper: 2181

✅ **Topics 已存在**
- orders
- inventory_updates
- vehicle_locations
- 等等...

✅ **费用: $0**（完全免费）

