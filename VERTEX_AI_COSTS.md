# Vertex AI 费用说明

## 当前使用情况

### ✅ 好消息：目前没有产生 Vertex AI 费用

**原因：**
1. **使用统计基线模型**：系统当前使用的是统计基线模型，不调用 Vertex AI API
2. **未配置端点**：`VERTEX_AI_ENDPOINT_ID` 为空，系统自动回退到本地统计模型
3. **GCP 计费未启用**：即使调用 Vertex AI API，由于计费未启用，也不会产生费用

### 代码实现

在 `ai-inference/vertex_ai_service.py` 中：

```python
def predict_with_vertex_ai(self, features: List[float]) -> Dict[str, Any]:
    """Predict using Vertex AI endpoint"""
    if not self.endpoint:  # 如果没有配置端点
        return self.predict("", "", 12, 1, [])  # 使用统计基线模型
    
    # 只有在配置了端点时才会调用 Vertex AI
    try:
        instances = [{"features": features}]
        response = self.endpoint.predict(instances=instances)
        # ...
```

**当前行为：**
- ✅ 使用 `predict()` 方法（统计基线，免费）
- ❌ 不使用 `predict_with_vertex_ai()` 方法（需要 Vertex AI，收费）

## Vertex AI 费用结构

### 如果使用 Vertex AI（当前未使用）

| 服务 | 费用 | 说明 |
|------|------|------|
| **API 调用** | $0.001-0.01/次 | 每次预测调用 |
| **模型训练** | $10-100/模型 | 一次性费用 |
| **端点部署** | $50-200/月 | 每个部署的端点 |
| **存储** | $0.10/GB/月 | 模型存储 |
| **网络** | $0.12/GB | 数据传输 |

### 估算示例

如果每天调用 10,000 次预测：
- API 调用：10,000 × $0.005 = **$50/天** = **~$1,500/月**
- 端点费用：**$50-200/月**
- **总计：~$1,550-1,700/月**

## 当前配置检查

### 1. 检查 Vertex AI 端点配置

```bash
cat .env | grep VERTEX_AI_ENDPOINT_ID
```

如果为空，说明**未使用 Vertex AI**，不会产生费用。

### 2. 检查实际调用

```bash
# 查看代码是否调用 Vertex AI
grep -r "predict_with_vertex_ai\|endpoint.predict" ai-inference/
```

### 3. 检查 GCP 计费状态

```bash
gcloud billing projects describe baisiyou
```

如果计费未启用，**即使调用也不会产生费用**。

## 费用控制建议

### 选项 1：继续使用统计基线（推荐，当前状态）
- ✅ **费用：$0**
- ✅ 功能完整，满足开发/测试需求
- ✅ 无需配置

### 选项 2：使用 Vertex AI（生产环境）
- ⚠️ **费用：~$1,500-2,000/月**
- ✅ 更准确的预测
- ✅ 可训练自定义模型
- ⚠️ 需要启用 GCP 计费

### 选项 3：混合使用
- 开发/测试：统计基线（免费）
- 生产环境：Vertex AI（付费）

## 如何确认是否产生费用

### 1. 检查 GCP 账单
```
https://console.cloud.google.com/billing?project=baisiyou
```

### 2. 检查 Vertex AI 使用情况
```bash
# 如果计费已启用
gcloud ai operations list --region=us-central1 --project=baisiyou
```

### 3. 检查代码调用
```bash
# 查看日志中是否有 Vertex AI 调用
grep -i "vertex\|endpoint.predict" logs/*.log
```

## 总结

### ✅ 当前状态：**没有 Vertex AI 费用**

**原因：**
1. 使用统计基线模型（不调用 Vertex AI API）
2. 未配置 Vertex AI 端点
3. GCP 计费未启用

**费用：$0**

### ⚠️ 如果将来使用 Vertex AI

**需要：**
1. 启用 GCP 计费账户
2. 配置 `VERTEX_AI_ENDPOINT_ID`
3. 训练和部署模型

**预计费用：~$1,500-2,000/月**（取决于调用量）

## 建议

对于当前开发/测试阶段：
- ✅ **继续使用统计基线模型**（免费且功能完整）
- ✅ 无需担心 Vertex AI 费用
- ✅ 生产环境时再考虑升级到 Vertex AI

