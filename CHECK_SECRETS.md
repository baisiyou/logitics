# 🔐 检查 GitHub Secrets 设置

## 必需的环境变量

为了前端能够连接到 Render 后端，您必须在 GitHub 中设置以下 Secret：

## 📋 设置步骤

### 1. 进入 Secrets 设置页面

访问：https://github.com/baisiyou/logitics/settings/secrets/actions

### 2. 检查是否已有 Secret

查找名为 `REACT_APP_API_URL` 的 Secret。

### 3. 如果没有，创建新的 Secret

1. 点击 **New repository secret** 按钮
2. **Name**: `REACT_APP_API_URL`
3. **Value**: `https://logitics.onrender.com`
4. 点击 **Add secret**

### 4. 如果已存在，检查值是否正确

1. 点击 `REACT_APP_API_URL` 查看或编辑
2. 确认值为：`https://logitics.onrender.com`
3. 如果值不正确，更新它

## ✅ 验证设置

设置完成后：

1. 进入 **Actions** 标签：https://github.com/baisiyou/logitics/actions
2. 选择 "Deploy to GitHub Pages" workflow
3. 点击 **Run workflow** → **Run workflow**
4. 等待部署完成
5. 访问前端页面：https://baisiyou.github.io/logitics/

## 🔍 如何确认 Secret 是否正确使用

在 GitHub Actions 构建日志中：

1. 展开 **Build** 步骤
2. 查看环境变量部分
3. 应该看到 `REACT_APP_API_URL` 被设置为 `https://logitics.onrender.com`

**注意**：出于安全考虑，GitHub Actions 日志中不会显示 Secret 的实际值，只会显示 `***`。

## ⚠️ 重要提示

- Secret 必须在 **Actions** 中使用，不是在其他地方
- 如果 Secret 不存在，构建会使用默认值 `http://localhost:8001`
- 设置 Secret 后必须重新部署才能生效

