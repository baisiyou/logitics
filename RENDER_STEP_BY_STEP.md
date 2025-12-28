# Render 部署 - 逐步指南

## 📍 在 Render Dashboard 中查找设置

### 如果您正在创建新服务：

1. **登录 Render**: https://dashboard.render.com
2. **点击 "New +"** 按钮（通常在右上角或左上角）
3. **选择 "Web Service"**
4. **连接 GitHub 仓库**: 选择 `baisiyou/logitics`
5. **填写配置表单** - 您会看到类似这样的表单：

   ```
   Name: [输入框]
   Region: [下拉菜单]
   Branch: [输入框]
   Root Directory: [输入框] ← 这里填写: applications/scheduler
   Environment: [下拉菜单] ← 这里选择: Python 3
   Build Command: [输入框] ← 这里填写: pip install --upgrade pip && pip install -r requirements.txt
   Start Command: [输入框] ← 这里填写: python dispatch_center.py
   ```

6. **添加环境变量** - 在表单中会有一个 **"Add Environment Variable"** 按钮或部分
   - Key: `CONFLUENT_BOOTSTRAP_SERVERS`
   - Value: 您的 Kafka 地址

### 如果您已经创建了服务：

1. **进入服务详情页** - 点击服务名称
2. **点击 "Settings" 标签**（通常在页面顶部，与其他标签如 "Logs", "Metrics" 并列）
3. **在 Settings 页面中**，您应该能看到：
   - **Build & Deploy** 部分
   - **Environment** 部分
   - **Environment Variables** 部分

## ⚠️ 如果仍然找不到

可能是因为 Render 的免费计划界面不同。请告诉我：

1. 您在 Render Dashboard 中看到了什么页面？
2. 创建服务时，表单中有哪些字段？
3. 或者您可以尝试以下方法：

## 🔧 替代方案：使用简化版（无需系统依赖）

由于 `confluent-kafka` 需要系统库，而 Render 可能无法安装，我们可以：

1. **使用 kafka-python** 替代（纯 Python 实现，无需系统依赖）
2. 但需要修改代码

**您希望我帮您创建使用 kafka-python 的版本吗？**

这样就不需要 Docker 或系统依赖了，但性能会稍微低一些。

## 📝 或者，告诉我您看到的具体内容

请描述一下：
- 您在哪个页面？
- 页面上有哪些按钮或选项？
- 错误信息是什么？（如果有的话）

这样我可以提供更准确的指导。

