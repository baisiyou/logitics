#!/bin/bash

# Setup gcloud environment variables

echo "=========================================="
echo "设置 gcloud 环境变量"
echo "=========================================="

# Check if gcloud is installed
if [ ! -f "$HOME/google-cloud-sdk/bin/gcloud" ]; then
    echo "❌ gcloud 未安装"
    echo "请先运行: ./deployment/cloud/install-gcloud-manual.sh"
    exit 1
fi

# Add to .zshrc if not already there
if ! grep -q "google-cloud-sdk" ~/.zshrc; then
    echo ""
    echo "添加到 ~/.zshrc..."
    echo "" >> ~/.zshrc
    echo "# Google Cloud SDK" >> ~/.zshrc
    echo 'export PATH="$HOME/google-cloud-sdk/bin:$PATH"' >> ~/.zshrc
    echo 'export CLOUDSDK_PYTHON=$(which python3)' >> ~/.zshrc
    echo "✅ 已添加到 ~/.zshrc"
    echo ""
    echo "请运行以下命令使配置生效:"
    echo "  source ~/.zshrc"
    echo ""
    echo "或者在新终端窗口中运行:"
    echo "  export PATH=\"\$HOME/google-cloud-sdk/bin:\$PATH\""
    echo "  export CLOUDSDK_PYTHON=\$(which python3)"
else
    echo "✅ PATH 已在 ~/.zshrc 中配置"
fi

# Set for current session
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

echo ""
echo "当前会话已配置，测试 gcloud..."
gcloud --version | head -1

echo ""
echo "=========================================="
echo "✅ 配置完成"
echo "=========================================="
echo ""
echo "现在可以使用 gcloud 命令:"
echo "  gcloud container clusters list"
echo "  gcloud projects list"
echo ""

