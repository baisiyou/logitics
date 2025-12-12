#!/bin/bash

# Install Google Cloud SDK

set -e

OS=$(uname -s)

echo "=========================================="
echo "Installing Google Cloud SDK"
echo "OS: ${OS}"
echo "=========================================="

if [ "$OS" = "Darwin" ]; then
    # macOS
    echo "Installing for macOS..."
    
    # Check if Homebrew is installed
    if command -v brew >/dev/null 2>&1; then
        echo "Using Homebrew to install..."
        
        # Set Python version for gcloud
        PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [ -n "$PYTHON_VERSION" ]; then
            export CLOUDSDK_PYTHON=$(which python3)
            echo "Using Python: $CLOUDSDK_PYTHON"
        fi
        
        # Try installing with Homebrew
        if ! brew install --cask google-cloud-sdk; then
            echo "Homebrew installation failed. Trying manual install..."
            curl https://sdk.cloud.google.com | bash
            exec -l $SHELL
        fi
    else
        echo "Homebrew not found. Installing manually..."
        curl https://sdk.cloud.google.com | bash
        exec -l $SHELL
    fi
elif [ "$OS" = "Linux" ]; then
    # Linux
    echo "Installing for Linux..."
    
    # Add Cloud SDK distribution URI
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    
    # Import the Google Cloud Platform public key
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    
    # Update and install
    sudo apt-get update && sudo apt-get install google-cloud-sdk
else
    echo "Unsupported OS: ${OS}"
    echo "Please install manually from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Initialize: gcloud init"
echo "  2. Login: gcloud auth login"
echo "  3. Set project: gcloud config set project YOUR_PROJECT_ID"
echo ""
echo "Or use alternative deployment methods:"
echo "  - Docker Compose (local)"
echo "  - AWS EKS"
echo "  - Azure AKS"

