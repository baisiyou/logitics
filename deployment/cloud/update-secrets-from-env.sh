#!/bin/bash

# Update Kubernetes secrets from .env file

set -e

ENV_FILE="${1:-.env}"
SECRETS_FILE="deployment/cloud/k8s/secrets.yaml"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

echo "=========================================="
echo "Updating Kubernetes secrets from .env"
echo "=========================================="

# Source the .env file
set -a
source "$ENV_FILE"
set +a

# Create a temporary secrets file
TEMP_SECRETS=$(mktemp)

cat > "$TEMP_SECRETS" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: logistics-secrets
  namespace: logistics-system
type: Opaque
stringData:
  CONFLUENT_API_KEY: "${CONFLUENT_API_KEY:-your-api-key}"
  CONFLUENT_API_SECRET: "${CONFLUENT_API_SECRET:-your-api-secret}"
  GOOGLE_CLOUD_PROJECT: "${GOOGLE_CLOUD_PROJECT:-your-project-id}"
  GOOGLE_APPLICATION_CREDENTIALS: "${GOOGLE_APPLICATION_CREDENTIALS:-base64-encoded-credentials}"
  POSTGRES_USER: "${POSTGRES_USER:-logistics_user}"
  POSTGRES_PASSWORD: "${POSTGRES_PASSWORD:-your-secure-password}"
  VERTEX_AI_LOCATION: "${VERTEX_AI_LOCATION:-us-central1}"
  BIGQUERY_DATASET: "${BIGQUERY_DATASET:-logistics_analytics}"
  CONFLUENT_BOOTSTRAP_SERVERS: "${CONFLUENT_BOOTSTRAP_SERVERS:-localhost:9092}"
  CONFLUENT_SCHEMA_REGISTRY_URL: "${CONFLUENT_SCHEMA_REGISTRY_URL:-http://localhost:8081}"
  AI_SERVICE_URL: "${AI_SERVICE_URL:-http://localhost:8000}"
EOF

# If GOOGLE_APPLICATION_CREDENTIALS is a file path, encode it
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Encoding GCP credentials file..."
    ENCODED_CREDS=$(base64 < "$GOOGLE_APPLICATION_CREDENTIALS" | tr -d '\n')
    sed -i '' "s|GOOGLE_APPLICATION_CREDENTIALS:.*|GOOGLE_APPLICATION_CREDENTIALS: \"${ENCODED_CREDS}\"|" "$TEMP_SECRETS"
fi

# Backup original file
if [ -f "$SECRETS_FILE" ]; then
    cp "$SECRETS_FILE" "${SECRETS_FILE}.backup"
    echo "Backed up original secrets file to ${SECRETS_FILE}.backup"
fi

# Update secrets file
mv "$TEMP_SECRETS" "$SECRETS_FILE"

echo ""
echo "✅ Updated $SECRETS_FILE with values from $ENV_FILE"
echo ""
echo "Values updated:"
echo "  - CONFLUENT_API_KEY: ${CONFLUENT_API_KEY:0:10}..."
echo "  - GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT}"
echo "  - POSTGRES_USER: ${POSTGRES_USER}"
echo "  - VERTEX_AI_LOCATION: ${VERTEX_AI_LOCATION}"
echo ""
echo "⚠️  Please review the secrets file before deploying:"
echo "   cat $SECRETS_FILE"

