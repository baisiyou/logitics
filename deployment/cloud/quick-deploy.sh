#!/bin/bash

# Quick deploy script with all prerequisites

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

cd "$(dirname "$0")/../.."

echo "=========================================="
echo "Quick GKE Deployment"
echo "=========================================="

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    echo "⚠️  Not authenticated. Opening browser for login..."
    gcloud auth login
fi

# Set project
gcloud config set project baisiyou

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable \
    container.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    --quiet

# Run main deployment
./deployment/cloud/deploy-to-gke.sh

