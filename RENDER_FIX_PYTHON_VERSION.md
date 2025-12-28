# 🔧 修复 Python 版本问题 - 重要！

## ⚠️ 问题

当前错误是因为 Render 使用了 Python 3.13，但 `pydantic 1.10.13` 不支持 Python 3.13。

## ✅ 解决方案：在 Render Dashboard 中设置 Python 3.11

### 步骤 1：进入服务设置

1. 登录 https://dashboard.render.com
2. 点击您的服务名称 `logistics-dispatch-center`
3. 点击页面顶部的 **Settings** 标签

### 步骤 2：添加环境变量

1. 在 Settings 页面，找到 **Environment Variables** 部分
2. 点击 **Add Environment Variable** 按钮
3. 添加以下环境变量：

   **Key**: `PYTHON_VERSION`  
   **Value**: `3.11.0`

4. 点击 **Save Changes**

### 步骤 3：重新部署

1. 点击页面顶部的 **Manual Deploy** 标签
2. 点击 **Clear build cache & deploy** 按钮
3. 等待重新构建和部署

## 📋 验证

部署后，在 **Logs** 标签页中应该看到：

```
Python 3.11.x
```

而不是：

```
Python 3.13.x
```

## 🎯 如果找不到 Environment Variables

如果在 Settings 页面找不到 Environment Variables：

1. 尝试在创建服务时设置（如果还没创建）
2. 或者查看页面是否有 **Environment** 或 **Configuration** 部分
3. 或者尝试删除服务后重新创建，在创建时设置环境变量

## 📝 完整的必需环境变量列表

在 Render Dashboard 中，您需要设置以下环境变量：

| Key | Value | 说明 |
|-----|-------|------|
| `PYTHON_VERSION` | `3.11.0` | **必需！** Python 版本 |
| `CONFLUENT_BOOTSTRAP_SERVERS` | `your-kafka-server:9092` | Kafka 服务器地址 |

## ✅ 完成

设置完成后，服务应该可以正常启动了！

