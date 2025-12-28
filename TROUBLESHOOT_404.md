# 404 错误排查指南

如果您看到所有 API 请求都返回 404，请按照以下步骤排查：

## 🔍 问题症状

- 所有 API 请求返回 404
- 错误信息显示类似 `statistics:1 Failed to load resource: the server responded with a status of 404`
- WebSocket 连接关闭

## ✅ 后端验证

首先验证后端 API 是否正常工作：

### 测试后端端点

在浏览器或终端中测试：

```bash
# 测试 status 端点
curl https://logitics.onrender.com/api/v1/status

# 测试 statistics 端点
curl https://logitics.onrender.com/api/v1/statistics

# 测试 orders 端点
curl https://logitics.onrender.com/api/v1/orders
```

如果这些请求都返回 JSON 数据，说明后端正常。

## 🔧 可能的原因

### 原因 1：环境变量未正确设置

**检查方法**：
1. 在浏览器中打开前端页面：https://baisiyou.github.io/logitics/
2. 按 F12 打开开发者工具
3. 在 Console 中输入：
   ```javascript
   console.log(process.env.REACT_APP_API_URL)
   ```
4. 或者查看构建后的代码（Ctrl+U 查看源代码），搜索 `localhost:8001` 或 `logitics.onrender.com`

**如果显示 `undefined` 或 `http://localhost:8001`**：
- GitHub Secret 没有正确设置
- 或者构建时没有使用 Secret

**解决方法**：
1. 确认 GitHub Secret 已设置：https://github.com/baisiyou/logitics/settings/secrets/actions
2. 确认 Secret 名称是 `REACT_APP_API_URL`（大小写敏感）
3. 确认 Secret 值是 `https://logitics.onrender.com`
4. 重新触发部署

### 原因 2：构建时环境变量未使用

**检查方法**：
1. 查看 GitHub Actions 构建日志
2. 在 Build 步骤中查找环境变量

**解决方法**：
- 确认 workflow 文件中的环境变量配置正确
- 重新触发部署

### 原因 3：浏览器缓存

**解决方法**：
1. 强制刷新：Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)
2. 清除浏览器缓存
3. 使用隐私模式/无痕模式访问

## 🔍 详细诊断步骤

### 步骤 1：检查浏览器 Network 标签

1. 打开前端页面
2. 按 F12 → Network 标签
3. 查看失败的请求
4. 检查 Request URL，应该类似：
   - ✅ 正确：`https://logitics.onrender.com/api/v1/statistics`
   - ❌ 错误：`/api/v1/statistics` 或 `statistics:1`

### 步骤 2：检查构建日志

1. 进入 GitHub Actions：https://github.com/baisiyou/logitics/actions
2. 查看最新的构建日志
3. 检查 Build 步骤是否成功
4. 查看是否有环境变量相关的错误

### 步骤 3：手动测试后端

```bash
# 测试各个端点
curl https://logitics.onrender.com/api/v1/status
curl https://logitics.onrender.com/api/v1/statistics
curl https://logitics.onrender.com/api/v1/orders
curl https://logitics.onrender.com/api/v1/vehicles
curl https://logitics.onrender.com/api/v1/alerts?limit=10
curl https://logitics.onrender.com/api/v1/demand-predictions
```

所有请求都应该返回 JSON 数据（即使数据为空）。

## ✅ 快速修复

1. **确认 GitHub Secret**：
   - 访问：https://github.com/baisiyou/logitics/settings/secrets/actions
   - 确认 `REACT_APP_API_URL` 存在
   - 确认值为 `https://logitics.onrender.com`

2. **重新触发部署**：
   - 访问：https://github.com/baisiyou/logitics/actions
   - 选择 "Deploy to GitHub Pages"
   - 点击 "Run workflow"

3. **清除浏览器缓存并刷新**

4. **检查 Network 标签确认请求 URL 正确**

## 📝 如果仍然无法解决

请提供：
1. 浏览器 Network 标签中的实际请求 URL
2. GitHub Actions 构建日志
3. 浏览器 Console 中的完整错误信息

