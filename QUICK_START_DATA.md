# 快速查看数据指南

## 🎯 当前状态

代码已更新！服务启动时会**自动生成模拟数据**，无需任何配置。

## ⏱️ 等待 Render 重新部署

由于代码已更新并推送到 GitHub，Render 会自动检测并重新部署服务。通常需要 **2-5 分钟**。

## ✅ 检查部署状态

1. 访问 Render Dashboard：https://dashboard.render.com
2. 查看 `logistics-dispatch-center` 服务的部署状态
3. 等待部署完成（状态变为 "Live"）

## 📊 查看数据

部署完成后，访问以下 URL：

### 前端（推荐）
```
https://baisiyou.github.io/logitics/
```

### 直接查看 API 数据
```
https://logitics.onrender.com/api/v1/status
```

如果看到包含 `orders`、`vehicles`、`warehouses` 等数据，说明数据已生成！

## 🔄 如果还是没有数据

如果部署完成后仍然没有数据，您可以手动触发：

```bash
curl -X POST https://logitics.onrender.com/api/v1/generate-mock-data
```

但正常情况下，服务启动时会自动生成，无需手动触发。

## 📝 说明

- **自动生成**：服务启动时如果没有 Kafka 配置，会自动生成 5-15 个订单、8-20 辆车、3 个仓库
- **无需配置**：不需要配置任何 Kafka 连接即可查看数据
- **实时更新**：数据会通过 WebSocket 实时推送到前端

现在请等待 Render 重新部署，然后访问前端查看数据！🎉

