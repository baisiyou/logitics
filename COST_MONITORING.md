# 费用监控指南

## 费用检查方法

### 1. Google Cloud Platform (GCP) 费用

#### 检查计费状态
```bash
# 检查是否启用计费
gcloud billing projects describe baisiyou

# 查看费用
# 访问: https://console.cloud.google.com/billing?project=baisiyou
```

#### 当前使用情况
- **Vertex AI API**: 如果使用，按调用次数计费 (~$0.001-0.01/次)
- **BigQuery**: 按查询数据量计费 (~$5/TB)
- **Compute Engine**: 如果创建了 VM，按使用时间计费
- **Container Registry**: 存储费用 (~$0.026/GB/月)

#### 免费额度
- **Vertex AI**: 无免费额度
- **BigQuery**: 每月 1TB 免费查询
- **Compute Engine**: f1-micro VM 在免费层内

### 2. Confluent Cloud 费用

#### 检查费用
访问: https://confluent.cloud/billing

#### 费用结构
- **Basic 计划**: ~$1/小时 (~$720/月)
- **Standard 计划**: ~$3-5/小时 (~$2160-3600/月)
- **数据吞吐量**: 超出计划限制后额外收费
- **存储**: 按存储量计费

#### 当前配置
从 `.env` 文件看，你使用的是 Confluent Cloud:
- Bootstrap Servers: `pkc-619z3.us-east1.gcp.confluent.cloud:9092`
- 需要检查 Confluent Cloud 控制台的费用

### 3. 本地服务费用

✅ **完全免费**
- 本地运行的 Python 服务
- Docker 容器（Kafka, PostgreSQL, Redis）
- 本地开发环境

## 费用估算

### 当前配置（本地 + Confluent Cloud）

| 服务 | 费用 | 说明 |
|------|------|------|
| 本地服务 | $0 | Python 服务、Docker 容器 |
| Confluent Cloud | ~$720-3600/月 | 取决于计划 |
| GCP (如果使用) | $0-50/月 | 取决于使用量 |
| **总计** | **~$720-3650/月** | 主要是 Confluent Cloud |

### 如果切换到完全本地

| 服务 | 费用 | 说明 |
|------|------|------|
| 本地服务 | $0 | 所有服务本地运行 |
| Docker Kafka | $0 | 本地 Docker Compose |
| **总计** | **$0** | 完全免费 |

## 如何减少费用

### 选项 1: 使用本地 Kafka
```bash
# 修改 .env 文件
CONFLUENT_BOOTSTRAP_SERVERS=localhost:9092

# 使用本地 Docker Compose
cd deployment
docker-compose up -d
```

### 选项 2: 使用 Confluent Cloud 免费层
- 检查是否有免费试用
- 使用 Basic 计划（最便宜）

### 选项 3: 监控和优化
- 监控数据吞吐量
- 优化 Kafka topic 配置
- 使用数据压缩
- 定期清理旧数据

## 费用监控脚本

运行费用检查脚本：
```bash
./scripts/check_costs.sh
```

## 重要提醒

1. **Confluent Cloud**: 如果使用，会产生持续费用
2. **GCP**: 只有在启用计费并使用服务时才收费
3. **本地服务**: 完全免费
4. **建议**: 开发/测试时使用本地 Kafka，生产环境再使用 Confluent Cloud

## 费用控制建议

1. **开发环境**: 使用本地 Docker Compose（免费）
2. **测试环境**: 使用 Confluent Cloud Basic 计划
3. **生产环境**: 根据需求选择合适计划
4. **设置预算警报**: 在 GCP 和 Confluent Cloud 中设置预算限制

