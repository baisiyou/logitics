# 前端问题诊断指南

如果前端页面显示为静态（数据不更新），请按照以下步骤检查：

## 🔍 步骤 1：检查环境变量是否设置

### 检查 GitHub Secret

1. 进入 GitHub 仓库：https://github.com/baisiyou/logitics
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 检查是否有 `REACT_APP_API_URL` secret
4. 确认值是否为：`https://logitics.onrender.com`

### 如果没有设置，请添加：

1. 点击 **New repository secret**
2. **Name**: `REACT_APP_API_URL`
3. **Value**: `https://logitics.onrender.com`
4. 点击 **Add secret**

### 设置后重新部署

1. 进入 **Actions** 标签
2. 选择最新的 "Deploy to GitHub Pages" workflow
3. 点击 **Run workflow** → **Run workflow**
4. 等待部署完成

## 🔍 步骤 2：检查浏览器控制台

1. 打开前端页面：https://baisiyou.github.io/logitics/
2. 按 `F12` 打开开发者工具
3. 切换到 **Console** 标签
4. 查看是否有错误信息

### 常见错误：

- **CORS 错误**：后端 CORS 配置问题（代码中已配置允许所有来源）
- **网络错误**：无法连接到后端
- **404 错误**：API 端点不存在
- **WebSocket 错误**：WebSocket 连接失败

## 🔍 步骤 3：检查后端是否正常运行

访问后端 API 端点：
```
https://logitics.onrender.com/api/v1/status
```

应该返回 JSON 数据。如果返回空数据，这是正常的（因为后端需要 Kafka 数据源）。

## 🔍 步骤 4：检查前端构建配置

### 检查构建时的环境变量

1. 进入 GitHub Actions：https://github.com/baisiyou/logitics/actions
2. 查看最新的构建日志
3. 搜索 "REACT_APP_API_URL" 或 "Build" 步骤
4. 确认构建时使用的环境变量值

### 手动验证构建产物

如果可能，检查构建后的代码：

1. 前端代码会编译环境变量到 JavaScript 中
2. 可以在浏览器中查看源代码（`Ctrl+U` 或右键查看页面源代码）
3. 搜索 `localhost:8001` 或 `logitics.onrender.com`
4. 如果找到 `localhost:8001`，说明环境变量没有正确设置

## 🔍 步骤 5：后端数据为空是正常的

**重要**：即使前端正确连接到后端，如果后端没有 Kafka 数据源，数据也会显示为空。

后端需要：
1. Kafka 服务器运行
2. 数据生产者（simulators）发送数据
3. 数据才会显示在前端

这是正常的！前端和后端的连接是成功的，只是没有数据源。

## 🔧 快速修复步骤

### 如果环境变量未设置：

```bash
# 1. 在 GitHub 中添加 Secret
# Settings → Secrets and variables → Actions → New repository secret
# Name: REACT_APP_API_URL
# Value: https://logitics.onrender.com

# 2. 触发重新部署
# Actions → Deploy to GitHub Pages → Run workflow
```

### 如果想测试完整功能：

后端需要 Kafka 数据源。您可以：
1. 使用 Confluent Cloud（推荐）
2. 或者本地运行 Kafka
3. 运行数据生成器（simulators）

## ✅ 验证连接成功

如果前端正确连接到后端，您应该看到：
- 页面正常显示（即使数据为0）
- 浏览器控制台没有网络错误
- WebSocket 连接建立（在 Network 标签中可以看到 WebSocket 连接）

## 📝 检查清单

- [ ] GitHub Secret `REACT_APP_API_URL` 已设置
- [ ] Secret 值为 `https://logitics.onrender.com`
- [ ] 已触发重新部署
- [ ] 浏览器控制台没有错误
- [ ] 后端 API 可以访问
- [ ] 理解后端数据为空是正常的（需要 Kafka 数据源）

