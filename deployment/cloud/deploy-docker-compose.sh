#!/bin/bash

# Alternative: Deploy using Docker Compose (no cloud account needed)

set -e

echo "=========================================="
echo "Deploying with Docker Compose"
echo "=========================================="

cd "$(dirname "$0")/.."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start infrastructure
echo "Starting infrastructure services..."
docker-compose -f deployment/docker-compose.yml up -d

# Wait for services
echo "Waiting for services to start..."
sleep 30

# Create Kafka topics
echo "Creating Kafka topics..."
python3 scripts/create_topics.py

# Build application images
echo "Building application images..."
docker build -f deployment/cloud/Dockerfile.vertex-ai -t vertex-ai-service:latest .
docker build -f deployment/cloud/Dockerfile.dispatch -t dispatch-service:latest .
docker build -f deployment/cloud/Dockerfile.dashboard -t dashboard:latest .

# Run services
echo "Starting application services..."

# Vertex AI Service
docker run -d \
  --name vertex-ai-service \
  --network deployment_default \
  -p 8000:8000 \
  -e CONFLUENT_BOOTSTRAP_SERVERS=kafka:9092 \
  vertex-ai-service:latest

# Dispatch Service
docker run -d \
  --name dispatch-service \
  --network deployment_default \
  -p 8001:8001 \
  -e CONFLUENT_BOOTSTRAP_SERVERS=kafka:9092 \
  dispatch-service:latest

# Dashboard
docker run -d \
  --name dashboard \
  --network deployment_default \
  -p 3000:80 \
  dashboard:latest

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Dispatch Center: http://localhost:8001"
echo "  - AI Service: http://localhost:8000"
echo ""
echo "To stop:"
echo "  docker stop vertex-ai-service dispatch-service dashboard"
echo "  docker-compose -f deployment/docker-compose.yml down"

