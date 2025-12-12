#!/bin/bash

# Manual Google Cloud SDK installation (fixes Python version issues)

set -e

echo "=========================================="
echo "Manual Google Cloud SDK Installation"
echo "=========================================="

# Find Python 3
PYTHON3_PATH=$(which python3)
if [ -z "$PYTHON3_PATH" ]; then
    echo "Error: Python 3 not found"
    exit 1
fi

PYTHON_VERSION=$($PYTHON3_PATH --version 2>&1 | cut -d' ' -f2)
echo "Found Python: $PYTHON3_PATH ($PYTHON_VERSION)"

# Set Python for gcloud
export CLOUDSDK_PYTHON=$PYTHON3_PATH

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ] || [ "$ARCH" = "aarch64" ]; then
    ARCH_TYPE="arm64"
else
    ARCH_TYPE="x86_64"
fi

# Download and install
echo "Downloading Google Cloud SDK for $ARCH_TYPE..."
cd /tmp
INSTALL_SCRIPT="/tmp/install-gcloud.sh"

# Use interactive installer instead
curl https://sdk.cloud.google.com > $INSTALL_SCRIPT
chmod +x $INSTALL_SCRIPT

# Set Python for the installer
export CLOUDSDK_PYTHON=$PYTHON3_PATH

echo "Installing (this may take a few minutes)..."
bash $INSTALL_SCRIPT --disable-prompts --install-dir=$HOME

# Add to PATH
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Add to your ~/.zshrc:"
echo "  export PATH=\"\$HOME/google-cloud-sdk/bin:\$PATH\""
echo "  export CLOUDSDK_PYTHON=$(which python3)"
echo ""
echo "Then run:"
echo "  source ~/.zshrc"
echo "  gcloud init"
echo "  gcloud auth login"

