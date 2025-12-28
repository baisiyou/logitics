# GitHub Pages 部署指南

本指南将帮助您将前端 Dashboard 部署到 GitHub Pages，并连接到 Render 上的后端服务。

## 📋 前置条件

1. GitHub 仓库（确保仓库是 public 或 GitHub Pro/Team 账户）
2. Render 后端服务已部署（例如：`https://your-app-name.onrender.com`）

## 🚀 部署步骤

### 1. 配置 GitHub Pages

1. 进入 GitHub 仓库的 **Settings** 页面
2. 在左侧菜单中找到 **Pages** 选项
3. 在 **Source** 下选择 **GitHub Actions**

### 2. 配置环境变量（可选）

如果您想在构建时设置后端 URL，可以在 GitHub 仓库的 **Settings** > **Secrets and variables** > **Actions** 中添加：

- **Name**: `REACT_APP_API_URL`
- **Value**: `https://your-app-name.onrender.com`

如果不设置，代码会使用默认值 `http://localhost:8001`（仅适用于本地开发）。

### 3. 推送代码触发部署

将代码推送到 `main` 分支，GitHub Actions 会自动：

1. 安装依赖
2. 构建 React 应用
3. 部署到 GitHub Pages

```bash
git add .
git commit -m "配置 GitHub Pages 部署"
git push origin main
```

### 4. 访问您的应用

部署完成后，您可以在以下地址访问应用：

```
https://your-username.github.io/your-repo-name/
```

## 🔧 本地开发

### 使用环境变量文件

在 `applications/dashboard` 目录下创建 `.env` 文件：

```bash
cd applications/dashboard
echo "REACT_APP_API_URL=http://localhost:8001" > .env
```

### 连接到 Render 后端

如果要在本地开发时连接到 Render 后端，修改 `.env` 文件：

```bash
REACT_APP_API_URL=https://your-app-name.onrender.com
```

然后重新启动开发服务器：

```bash
npm start
```

## 🌐 生产环境配置

### 在 GitHub Actions 中配置

1. 进入 GitHub 仓库的 **Settings** > **Secrets and variables** > **Actions**
2. 点击 **New repository secret**
3. 添加以下 secret：
   - **Name**: `REACT_APP_API_URL`
   - **Value**: 您的 Render 后端 URL（例如：`https://your-app-name.onrender.com`）

### 手动配置构建环境变量

如果需要，您也可以直接修改 `.github/workflows/deploy-pages.yml` 文件中的环境变量部分：

```yaml
env:
  REACT_APP_API_URL: ${{ secrets.REACT_APP_API_URL || 'https://your-default-render-url.onrender.com' }}
```

## 🔍 故障排除

### 页面显示空白

1. 检查浏览器控制台是否有错误
2. 确认 `package.json` 中的 `homepage` 字段设置为 `"."`
3. 检查构建是否成功完成

### API 连接失败

1. 确认 Render 后端服务正在运行
2. 检查后端 URL 是否正确配置
3. 确认 Render 后端已启用 CORS，允许来自 GitHub Pages 域名的请求

### WebSocket 连接失败

1. 确认 Render 后端支持 WebSocket（可能需要配置）
2. 检查 WebSocket URL 是否正确（HTTP 使用 `ws://`，HTTPS 使用 `wss://`）
3. 代码会自动根据 API URL 协议转换 WebSocket URL

## 📝 注意事项

1. GitHub Pages 只支持静态网站，所有后端逻辑必须在 Render 上运行
2. 确保 Render 后端已配置 CORS，允许来自 GitHub Pages 的请求
3. 如果您的仓库是私有的，需要 GitHub Pro/Team 账户才能使用 GitHub Pages
4. 首次部署可能需要几分钟时间

## 🔗 相关链接

- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [Render 文档](https://render.com/docs)
- [React 环境变量](https://create-react-app.dev/docs/adding-custom-environment-variables/)

