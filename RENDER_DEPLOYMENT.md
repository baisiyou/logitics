# Render 部署指南

本指南将帮助您将后端服务部署到 Render 平台。

## 📋 前置条件

1. Render 账户（免费注册：https://render.com）
2. GitHub 仓库已连接到 Render（推荐）
3. Confluent Cloud 账户或 Kafka 集群（用于消息队列）

## 🚀 部署步骤

### 方法一：通过 Render Dashboard 部署（推荐）

#### 1. 创建新的 Web Service（推荐使用 Dockerfile）

由于 `confluent-kafka` 需要系统依赖（librdkafka），**强烈推荐使用 Dockerfile**：

1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击 **New +** → **Web Service**
3. 连接您的 GitHub 仓库：`baisiyou/logitics`
4. 填写服务配置：
   - **Name**: `logistics-dispatch-center`
   - **Environment**: 选择 **Docker**（重要！）
   - **Dockerfile Path**: `applications/scheduler/Dockerfile`
   - **Docker Context**: `.`（项目根目录）
   - **Region**: `Oregon (US West)` 或其他您偏好的区域
   - **Branch**: `main`
   - **Plan**: `Free`（免费版，适合测试）

**备选方法**：如果无法使用 Docker，可以尝试：
   - **Environment**: `Python 3`
   - **Root Directory**: `applications/scheduler`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python dispatch_center.py`

**注意**：Python 环境方法可能会失败，因为缺少 `librdkafka-dev` 系统库。

#### 2. 配置环境变量

在 **Environment Variables** 部分添加：

| Key | Value | 说明 |
|-----|-------|------|
| `CONFLUENT_BOOTSTRAP_SERVERS` | `your-kafka-bootstrap-server:9092` | Kafka 服务器地址 |
| `PYTHON_VERSION` | `3.11.0` | **必需！** Python 版本（必须使用 3.11，pydantic 1.10.13 不支持 Python 3.13） |

**重要说明**：
- `PORT` 环境变量由 Render 自动设置，无需手动配置
- 如果您使用 Confluent Cloud，格式为：`pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`
- 如果使用本地 Kafka，需要确保 Kafka 可以从互联网访问（不推荐用于生产环境）

#### 3. 配置 Confluent Cloud（如果使用）

如果使用 Confluent Cloud，还需要配置认证：

1. 在 Render Dashboard 中添加环境变量：
   - `CONFLUENT_API_KEY`: 您的 Confluent API Key
   - `CONFLUENT_API_SECRET`: 您的 Confluent API Secret

2. 修改 `dispatch_center.py` 以支持 SASL 认证（如果需要）：
   ```python
   consumer = Consumer({
       'bootstrap.servers': BOOTSTRAP_SERVERS,
       'group.id': 'dispatch-center',
       'auto.offset.reset': 'earliest',
       'security.protocol': 'SASL_SSL',
       'sasl.mechanisms': 'PLAIN',
       'sasl.username': os.getenv('CONFLUENT_API_KEY'),
       'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
   })
   ```

#### 4. 部署和验证

1. 点击 **Create Web Service**
2. 等待构建和部署完成（通常需要 2-5 分钟）
3. 部署成功后，您将获得一个 URL，例如：`https://logistics-dispatch-center.onrender.com`
4. 访问健康检查端点：`https://your-service.onrender.com/api/v1/status`

### 方法二：使用 render.yaml（高级）

如果您想使用配置文件方式部署：

1. 确保 `render.yaml` 文件在仓库根目录
2. 在 Render Dashboard 中选择 **New +** → **Blueprint**
3. 连接您的 GitHub 仓库
4. Render 会自动读取 `render.yaml` 配置

**注意**：使用 `render.yaml` 时，需要调整路径，因为 Render 会在仓库根目录执行构建命令。

## 🔧 配置 GitHub Pages 连接

部署完成后，您需要将 GitHub Pages 前端连接到 Render 后端：

### 1. 获取 Render 服务 URL

部署完成后，Render 会提供一个 URL，例如：
```
https://logistics-dispatch-center.onrender.com
```

### 2. 在 GitHub 中配置环境变量

1. 进入您的 GitHub 仓库：https://github.com/baisiyou/logitics/settings/secrets/actions
2. 添加 Secret：
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://logistics-dispatch-center.onrender.com`

### 3. 重新触发部署

推送一个空提交或手动触发 GitHub Actions 来重新构建前端：

```bash
git commit --allow-empty -m "触发 GitHub Pages 部署"
git push origin main
```

## 🌐 WebSocket 支持

Render 的免费计划支持 WebSocket，但需要注意：

1. **空闲服务休眠**：免费计划的服务在 15 分钟无活动后会休眠，首次访问需要几秒钟启动
2. **WebSocket 连接**：代码已自动处理 HTTP/HTTPS 到 WS/WSS 的转换
3. **连接超时**：如果服务休眠，WebSocket 连接可能会中断，前端代码需要处理重连

## 📝 环境变量参考

### 必需的环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `CONFLUENT_BOOTSTRAP_SERVERS` | Kafka 服务器地址 | `localhost:9092` 或 `pkc-xxxxx.confluent.cloud:9092` |
| `PORT` | 服务端口（Render 自动设置） | 自动设置，无需配置 |

### 可选的环境变量（如果使用 Confluent Cloud）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `CONFLUENT_API_KEY` | Confluent API Key | - |
| `CONFLUENT_API_SECRET` | Confluent API Secret | - |

## 🔍 故障排除

### 问题 1：构建失败

**症状**：构建过程中出现错误

**解决方案**：
- 检查 `requirements.txt` 是否包含所有依赖
- 确保 Python 版本为 3.11
- 查看 Render 日志了解详细错误信息

### 问题 2：服务启动后立即崩溃

**症状**：服务部署成功但无法访问

**解决方案**：
- 检查 `CONFLUENT_BOOTSTRAP_SERVERS` 是否正确配置
- 确保 Kafka 服务器可以从互联网访问
- 查看 Render 日志：`https://dashboard.render.com/web/your-service/logs`

### 问题 3：Kafka 连接失败

**症状**：服务运行但无法连接到 Kafka

**解决方案**：
- 确认 Kafka 服务器地址正确
- 如果使用 Confluent Cloud，检查认证信息
- 确认网络连接（防火墙、VPN 等）
- 考虑使用 Confluent Cloud 的公共端点

### 问题 4：WebSocket 连接失败

**症状**：前端无法建立 WebSocket 连接

**解决方案**：
- 确认后端 URL 使用 HTTPS（Render 自动提供）
- 检查前端代码是否正确转换为 WSS
- 查看浏览器控制台的错误信息
- 确认 Render 服务正在运行（免费计划可能休眠）

### 问题 5：CORS 错误

**症状**：前端请求被 CORS 策略阻止

**解决方案**：
- 代码中已配置 CORS 允许所有来源（`allow_origins=["*"]`）
- 如果仍有问题，检查 Render 的代理设置

## 💰 费用说明

- **免费计划**：适合开发和测试
  - 服务在 15 分钟无活动后休眠
  - 每次访问需要几秒钟启动
  - 每月 750 小时运行时间
  
- **付费计划**：适合生产环境
  - 服务始终运行
  - 更好的性能
  - 更多资源

## 🔗 相关链接

- [Render 文档](https://render.com/docs)
- [Render 定价](https://render.com/pricing)
- [Confluent Cloud 文档](https://docs.confluent.io/cloud/current/overview.html)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)

## 📚 下一步

部署完成后，您可以：

1. 配置 GitHub Pages 前端连接到 Render 后端
2. 设置其他后端服务（customer、driver、warehouse）
3. 配置 CI/CD 自动部署
4. 设置监控和告警

祝您部署顺利！🚀

