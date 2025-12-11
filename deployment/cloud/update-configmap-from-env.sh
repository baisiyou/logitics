#!/bin/bash

# Update Kubernetes configmap from .env file

set -e

ENV_FILE="${1:-.env}"
CONFIGMAP_FILE="deployment/cloud/k8s/configmap.yaml"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

echo "=========================================="
echo "Updating Kubernetes configmap from .env"
echo "=========================================="

# Source the .env file
set -a
source "$ENV_FILE"
set +a

# Create updated configmap
cat > "$CONFIGMAP_FILE" <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: logistics-config
  namespace: logistics-system
data:
  CONFLUENT_BOOTSTRAP_SERVERS: "${CONFLUENT_BOOTSTRAP_SERVERS:-your-kafka-bootstrap-servers}"
  CONFLUENT_SCHEMA_REGISTRY_URL: "${CONFLUENT_SCHEMA_REGISTRY_URL:-http://schema-registry:8081}"
  AI_SERVICE_URL: "${AI_SERVICE_URL:-http://vertex-ai-service:8000}"
  DISPATCH_CENTER_URL: "${DISPATCH_CENTER_URL:-http://dispatch-service:8001}"
  POSTGRES_HOST: "${POSTGRES_HOST:-postgres-service}"
  POSTGRES_PORT: "${POSTGRES_PORT:-5432}"
  POSTGRES_DB: "${POSTGRES_DB:-logistics_db}"
  REDIS_HOST: "${REDIS_HOST:-redis-service}"
  REDIS_PORT: "${REDIS_PORT:-6379}"
  API_PORT: "${API_PORT:-8000}"
  DASHBOARD_PORT: "${DASHBOARD_PORT:-3000}"
  WEBSOCKET_PORT: "${WEBSOCKET_PORT:-8080}"
EOF

echo "✅ Updated $CONFIGMAP_FILE with values from $ENV_FILE"
echo ""
echo "Updated values:"
echo "  - CONFLUENT_BOOTSTRAP_SERVERS: ${CONFLUENT_BOOTSTRAP_SERVERS}"
echo "  - POSTGRES_HOST: ${POSTGRES_HOST}"
echo "  - REDIS_HOST: ${REDIS_HOST}"

