# 使用 Dockerfile 部署到 Render（推荐）

由于 `confluent-kafka` 需要系统依赖（librdkafka），推荐使用 Dockerfile 部署。

## 🚀 部署步骤

### 方法 1：使用 Dockerfile（推荐）

1. 在 Render Dashboard 中创建新的 **Web Service**
2. 连接到您的 GitHub 仓库
3. 在服务设置中：
   - **Dockerfile Path**: `applications/scheduler/Dockerfile`
   - **Docker Context**: `.`（项目根目录）
   - **Environment**: 选择 `Docker`
   - **Plan**: `Free`

4. 添加环境变量：
   - `CONFLUENT_BOOTSTRAP_SERVERS`: 您的 Kafka 服务器地址

5. 点击 **Create Web Service**

### 方法 2：使用 Docker Registry

如果您的 Render 计划支持，也可以：

1. 构建 Docker 镜像：
   ```bash
   cd applications/scheduler
   docker build -t logistics-dispatch:latest .
   ```

2. 推送到 Docker Hub 或其他 Registry

3. 在 Render 中使用该镜像

## 📝 注意事项

- Dockerfile 会自动安装所需的系统依赖（librdkafka-dev）
- 确保 Dockerfile 在正确的位置（`applications/scheduler/Dockerfile`）
- Render 会自动处理 PORT 环境变量

