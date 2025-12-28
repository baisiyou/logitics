# 生成模拟数据指南

现在您可以在没有 Kafka 的情况下查看真实的数据！

## 🎯 方法 1：自动生成（已启用）

如果后端没有配置 Kafka（使用默认值 `localhost:9092`），服务启动时会自动生成初始模拟数据。

## 🎯 方法 2：通过 API 生成

### 生成模拟数据

访问以下端点来生成新的模拟数据：

```
POST https://logitics.onrender.com/api/v1/generate-mock-data
```

或者在浏览器中访问（使用 GET，但建议用 POST 工具如 curl 或 Postman）：

```bash
curl -X POST https://logitics.onrender.com/api/v1/generate-mock-data
```

### 查看数据

生成数据后，访问前端页面：
```
https://baisiyou.github.io/logitics/
```

您应该能看到：
- 订单列表
- 车辆位置（在地图上）
- 统计数据
- 实时更新

## 🎯 方法 3：在代码中自动生成（已实现）

服务启动时会检查是否有 Kafka 配置，如果没有，会自动生成模拟数据。

## 📊 模拟数据包含

- **订单**：5-15 个随机订单
- **车辆**：8-20 辆车辆，包含位置、状态、速度等信息
- **仓库**：3 个仓库
- **统计数据**：自动计算和更新

## 🔄 更新数据

模拟数据是静态的（不会自动变化），如果需要更新：

1. 再次调用 `POST /api/v1/generate-mock-data` 端点
2. 或者配置真实的 Kafka 数据源（见 `KAFKA_SETUP_GUIDE.md`）

## ✅ 快速测试

1. 访问前端：https://baisiyou.github.io/logitics/
2. 如果没有数据，访问：https://logitics.onrender.com/api/v1/generate-mock-data
3. 刷新前端页面，应该能看到数据了！

现在您可以看到完整的系统功能了！🎉

