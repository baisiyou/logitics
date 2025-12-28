# Render 快速部署指南

## 🚀 5 分钟快速部署

### 步骤 1：准备 Render 账户

1. 访问 https://render.com
2. 使用 GitHub 账户登录（推荐）

### 步骤 2：创建 Web Service

1. 在 Render Dashboard 点击 **New +** → **Web Service**
2. 选择 **Build and deploy from a Git repository**
3. 连接您的 GitHub 仓库：`baisiyou/logitics`

### 步骤 3：配置服务

填写以下配置信息：

#### 基本信息
- **Name**: `logistics-dispatch-center`
- **Environment**: `Python 3`
- **Region**: `Oregon (US West)` 或您偏好的区域
- **Branch**: `main`
- **Root Directory**: `applications/scheduler` ⚠️ **重要！**

#### 构建和启动命令
- **Build Command**: 
  ```bash
  pip install -r ../../requirements.txt
  ```
  
- **Start Command**: 
  ```bash
  python dispatch_center.py
  ```

#### 计划
- **Instance Type**: `Free`（免费版，适合测试）

### 步骤 4：配置环境变量

点击 **Advanced** → **Add Environment Variable**，添加：

| Key | Value | 必需 |
|-----|-------|------|
| `CONFLUENT_BOOTSTRAP_SERVERS` | `your-kafka-server:9092` | ✅ 是 |
| `PYTHON_VERSION` | `3.11` | ❌ 否（可选） |

**注意**：
- `PORT` 环境变量由 Render 自动设置，**无需手动配置**
- 如果您还没有 Kafka 服务器，可以使用 Confluent Cloud 免费版

### 步骤 5：部署

1. 点击 **Create Web Service**
2. 等待构建完成（通常 2-5 分钟）
3. 部署成功后，Render 会提供一个 URL，例如：
   ```
   https://logistics-dispatch-center.onrender.com
   ```

### 步骤 6：验证部署

1. 访问您的服务 URL
2. 访问健康检查端点：
   ```
   https://your-service.onrender.com/api/v1/status
   ```
3. 应该返回 JSON 响应

### 步骤 7：连接 GitHub Pages 前端

1. 在 GitHub 仓库中添加 Secret：
   - 进入：https://github.com/baisiyou/logitics/settings/secrets/actions
   - 点击 **New repository secret**
   - Name: `REACT_APP_API_URL`
   - Value: `https://logistics-dispatch-center.onrender.com`（您的 Render URL）

2. 推送代码触发前端部署：
   ```bash
   git commit --allow-empty -m "触发部署"
   git push origin main
   ```

## ✅ 完成！

现在您的后端已部署到 Render，前端已部署到 GitHub Pages！

访问您的 GitHub Pages URL 查看完整应用。

## 🔧 常见问题

### Q: 服务启动后无法访问？

A: 检查环境变量 `CONFLUENT_BOOTSTRAP_SERVERS` 是否正确配置。查看日志：在 Render Dashboard 中点击服务 → Logs

### Q: 免费计划的服务很慢？

A: 免费计划的服务在 15 分钟无活动后会休眠，首次访问需要几秒钟启动。这是正常的。

### Q: 如何查看日志？

A: 在 Render Dashboard 中，点击您的服务 → Logs 标签页

### Q: 需要帮助？

A: 查看详细文档：`RENDER_DEPLOYMENT.md`

