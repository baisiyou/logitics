#!/bin/bash

# Build and push Docker images to Google Container Registry

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
REGION=${REGION:-"us-central1"}
GCR_REGISTRY="gcr.io/${PROJECT_ID}"

echo "=========================================="
echo "Building and pushing Docker images"
echo "Project: ${PROJECT_ID}"
echo "=========================================="

# Authenticate with GCR
echo "Authenticating with GCR..."
gcloud auth configure-docker

# Build and push Vertex AI service
echo "Building vertex-ai-service..."
docker build -f deployment/cloud/Dockerfile.vertex-ai -t ${GCR_REGISTRY}/vertex-ai-service:latest .
docker push ${GCR_REGISTRY}/vertex-ai-service:latest

# Build and push Dispatch service
echo "Building dispatch-service..."
docker build -f deployment/cloud/Dockerfile.dispatch -t ${GCR_REGISTRY}/dispatch-service:latest .
docker push ${GCR_REGISTRY}/dispatch-service:latest

# Build and push Dashboard
echo "Building dashboard..."
docker build -f deployment/cloud/Dockerfile.dashboard -t ${GCR_REGISTRY}/dashboard:latest .
docker push ${GCR_REGISTRY}/dashboard:latest

# Build simulators
echo "Building simulators..."
docker build -f deployment/cloud/Dockerfile.simulator -t ${GCR_REGISTRY}/order-simulator:latest --target order-simulator .
docker build -f deployment/cloud/Dockerfile.simulator -t ${GCR_REGISTRY}/vehicle-simulator:latest --target vehicle-simulator .
docker push ${GCR_REGISTRY}/order-simulator:latest
docker push ${GCR_REGISTRY}/vehicle-simulator:latest

echo "=========================================="
echo "All images built and pushed successfully!"
echo "=========================================="

