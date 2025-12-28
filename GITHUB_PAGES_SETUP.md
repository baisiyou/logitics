# GitHub Pages 部署快速设置指南

## 📝 概述

本项目的 Dashboard 前端已配置为可以部署到 GitHub Pages，后端服务可以部署到 Render。

## 🚀 快速开始

### 1. GitHub Pages 设置

1. **启用 GitHub Pages**：
   - 进入仓库 Settings → Pages
   - Source 选择 "GitHub Actions"

2. **配置环境变量（可选）**：
   - 进入 Settings → Secrets and variables → Actions
   - 添加 Secret：`REACT_APP_API_URL` = `https://your-render-app.onrender.com`
   - 如果不设置，将使用默认值（仅适用于本地开发）

3. **推送代码**：
   ```bash
   git push origin main
   ```

4. **等待部署完成**：
   - GitHub Actions 会自动构建并部署
   - 访问：`https://your-username.github.io/your-repo-name/`

### 2. Render 后端设置

确保您的后端服务在 Render 上：
- 已启用 CORS（代码中已配置为允许所有来源）
- WebSocket 端点正常工作（`/ws`）
- API 端点可访问（`/api/v1/*`）

## 📁 相关文件

- **Workflow**: `.github/workflows/deploy-pages.yml`
- **前端代码**: `applications/dashboard/`
- **详细文档**: `applications/dashboard/GITHUB_PAGES_DEPLOYMENT.md`

## ⚙️ 配置说明

### 环境变量

前端使用 `REACT_APP_API_URL` 环境变量来配置后端 URL：

- **本地开发**: `http://localhost:8001`（默认值）
- **生产环境**: `https://your-app-name.onrender.com`

### WebSocket 自动转换

代码会自动将 HTTP/HTTPS URL 转换为对应的 WebSocket URL：
- `http://` → `ws://`
- `https://` → `wss://`

## 🔧 故障排除

如果遇到问题，请查看详细文档：`applications/dashboard/GITHUB_PAGES_DEPLOYMENT.md`

