#!/bin/bash

# Sync all configuration from .env to Kubernetes manifests

set -e

ENV_FILE="${1:-.env}"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo "Usage: $0 [path-to-.env-file]"
    exit 1
fi

echo "=========================================="
echo "Syncing .env to Kubernetes Configuration"
echo "=========================================="
echo "Source: $ENV_FILE"
echo ""

# Update secrets
echo "1. Updating secrets..."
./deployment/cloud/update-secrets-from-env.sh "$ENV_FILE"

echo ""

# Update configmap
echo "2. Updating configmap..."
./deployment/cloud/update-configmap-from-env.sh "$ENV_FILE"

echo ""
echo "=========================================="
echo "✅ Sync complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Review the updated files:"
echo "     cat deployment/cloud/k8s/secrets.yaml"
echo "     cat deployment/cloud/k8s/configmap.yaml"
echo ""
echo "  2. Deploy to Kubernetes:"
echo "     ./deployment/cloud/deploy-gcp.sh"
echo ""

