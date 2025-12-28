# Kafka 数据源配置指南

本指南将帮助您配置 Kafka 数据源，使系统能够显示实时数据。

## 📋 选项概览

您可以选择以下任一方式：

1. **Confluent Cloud**（推荐，免费试用）
2. **本地 Kafka**（需要自己的服务器）
3. **其他托管 Kafka 服务**

## 🚀 选项 1：使用 Confluent Cloud（推荐）

### 步骤 1：注册 Confluent Cloud

1. 访问：https://www.confluent.io/confluent-cloud/tryfree/
2. 注册免费账号
3. 完成邮箱验证

### 步骤 2：创建 Kafka 集群

1. 登录 Confluent Cloud Dashboard
2. 点击 **Add Cluster** 或 **Create Cluster**
3. 选择 **Basic**（免费版）
4. 选择云服务提供商和区域（选择离您最近的）
5. 点击 **Launch Cluster**

### 步骤 3：获取连接信息

1. 在集群页面，点击 **Clients** 或 **Configuration**
2. 选择 **Java** 或 **Python** 客户端
3. 复制以下信息：
   - **Bootstrap servers**: 例如 `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`
   - **API Key** 和 **API Secret**（如果启用了 SASL 认证）

### 步骤 4：创建 Topics

在 Confluent Cloud 中创建以下 Topics：

1. 进入集群 → **Topics** → **Add Topic**
2. 创建以下 Topics（使用默认设置即可）：
   - `orders`
   - `vehicle_locations`
   - `warehouse_inventory_levels`
   - `demand_predictions`
   - `anomaly_alerts`
   - `warehouse_pressure_alerts`
   - `dispatch_assignments`

或者使用脚本创建（见下方）。

### 步骤 5：在 Render 中配置环境变量

1. 进入 Render Dashboard：https://dashboard.render.com
2. 找到您的服务：`logistics-dispatch-center`
3. 点击 **Environment** 标签
4. 添加/编辑以下环境变量：

   | Key | Value | 说明 |
   |-----|-------|------|
   | `CONFLUENT_BOOTSTRAP_SERVERS` | `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092` | 您的 Confluent Cloud bootstrap servers |

   如果启用了 SASL 认证，还需要添加：
   
   | Key | Value | 说明 |
   |-----|-------|------|
   | `CONFLUENT_API_KEY` | 您的 API Key | Confluent API Key |
   | `CONFLUENT_API_SECRET` | 您的 API Secret | Confluent API Secret |

5. 点击 **Save Changes**
6. Render 会自动重新部署服务

### 步骤 6：运行数据生成器

数据生成器可以在本地运行，向 Kafka 发送数据：

#### 方法 A：在本地运行（推荐用于测试）

1. **安装依赖**：
   ```bash
   cd /Users/zrb/Documents/logistics
   pip install -r requirements.txt
   ```

2. **配置环境变量**（创建 `.env` 文件）：
   ```bash
   cd /Users/zrb/Documents/logistics
   cat > .env << EOF
   CONFLUENT_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
   CONFLUENT_API_KEY=your-api-key
   CONFLUENT_API_SECRET=your-api-secret
   EOF
   ```

3. **创建 Topics**（如果还没有）：
   ```bash
   python scripts/create_topics.py
   ```

4. **运行数据生成器**：
   ```bash
   # 订单生成器
   python data-sources/simulators/order_simulator.py &
   
   # 车辆位置生成器
   python data-sources/simulators/vehicle_location_simulator.py &
   
   # 库存生成器
   python data-sources/simulators/inventory_simulator.py &
   ```

#### 方法 B：使用 Python 脚本批量运行

```bash
cd /Users/zrb/Documents/logistics
python -c "
import subprocess
import time

# 启动所有生成器
processes = [
    subprocess.Popen(['python', 'data-sources/simulators/order_simulator.py']),
    subprocess.Popen(['python', 'data-sources/simulators/vehicle_location_simulator.py']),
    subprocess.Popen(['python', 'data-sources/simulators/inventory_simulator.py'])
]

print('数据生成器已启动，按 Ctrl+C 停止')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
    print('已停止所有生成器')
"
```

### 步骤 7：验证数据流

1. **检查后端日志**（在 Render Dashboard）：
   - 应该看到 "Dispatch中心Kafka消费者AlreadyStart" 消息
   - 没有连接错误

2. **访问前端**：
   - https://baisiyou.github.io/logitics/
   - 应该看到数据实时更新

3. **检查 API**：
   ```bash
   curl https://logitics.onrender.com/api/v1/statistics
   curl https://logitics.onrender.com/api/v1/orders
   ```
   应该返回非空数据。

## 🔧 选项 2：使用本地 Kafka（仅用于开发测试）

### 步骤 1：启动本地 Kafka

使用 Docker Compose：

```bash
cd /Users/zrb/Documents/logistics/deployment
docker-compose up -d kafka zookeeper
```

### 步骤 2：配置 Render 环境变量

在 Render Dashboard 中设置：
- `CONFLUENT_BOOTSTRAP_SERVERS`: `your-public-ip:9092`

**注意**：需要确保您的本地 Kafka 可以从互联网访问（通常需要配置端口转发或 VPN），这对生产环境不推荐。

### 步骤 3：运行数据生成器

按照选项 1 的步骤 6 运行数据生成器。

## ⚠️ 关于 SASL 认证

如果 Confluent Cloud 启用了 SASL 认证，您需要：

1. **更新后端代码**以支持 SASL（如果需要）
2. 在 Render 环境变量中设置 `CONFLUENT_API_KEY` 和 `CONFLUENT_API_SECRET`

**注意**：当前代码使用的是 `kafka-python-ng`，它支持 SASL 认证。如果您的 Confluent Cloud 配置需要认证，可能需要修改代码以添加认证配置。

## 📝 快速测试（不使用 Kafka）

如果您只是想测试前端显示，可以临时在后端代码中添加模拟数据（仅用于演示）。

## ✅ 配置检查清单

- [ ] Confluent Cloud 账号已创建
- [ ] Kafka 集群已创建
- [ ] Topics 已创建
- [ ] Render 环境变量 `CONFLUENT_BOOTSTRAP_SERVERS` 已设置
- [ ] 如果需要，`CONFLUENT_API_KEY` 和 `CONFLUENT_API_SECRET` 已设置
- [ ] Render 服务已重新部署
- [ ] 数据生成器正在运行
- [ ] 前端显示数据

## 🔗 相关链接

- [Confluent Cloud 文档](https://docs.confluent.io/cloud/current/overview.html)
- [kafka-python 文档](https://kafka-python.readthedocs.io/)

