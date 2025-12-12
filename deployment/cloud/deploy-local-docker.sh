#!/bin/bash

# Alternative: Enhanced local Docker Compose deployment
# This runs everything locally but makes it accessible

set -e

cd "$(dirname "$0")/../.."

echo "=========================================="
echo "Local Docker Compose Deployment"
echo "=========================================="
echo ""
echo "This will deploy using Docker Compose locally"
echo "All services will run in containers"
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start infrastructure
echo "Starting infrastructure (Kafka, PostgreSQL, Redis)..."
cd deployment
docker-compose up -d

echo "Waiting for services to start..."
sleep 30

# Create Kafka topics
echo "Creating Kafka topics..."
cd ..
python3 scripts/create_topics.py

# Build application images
echo "Building application images..."
docker build -f deployment/cloud/Dockerfile.vertex-ai -t vertex-ai-service:latest .
docker build -f deployment/cloud/Dockerfile.dispatch -t dispatch-service:latest .
docker build -f deployment/cloud/Dockerfile.dashboard -t dashboard:latest .
docker build -f deployment/cloud/Dockerfile.simulator --target order-simulator -t order-simulator:latest .
docker build -f deployment/cloud/Dockerfile.simulator --target vehicle-simulator -t vehicle-simulator:latest .

# Stop existing containers
echo "Stopping existing containers..."
docker stop vertex-ai-service dispatch-service dashboard order-simulator vehicle-simulator 2>/dev/null || true
docker rm vertex-ai-service dispatch-service dashboard order-simulator vehicle-simulator 2>/dev/null || true

# Run services
echo "Starting application services..."

# Load .env
set -a
source .env
set +a

# Vertex AI Service
docker run -d \
  --name vertex-ai-service \
  --network deployment_default \
  -p 8000:8000 \
  -e CONFLUENT_BOOTSTRAP_SERVERS=${CONFLUENT_BOOTSTRAP_SERVERS:-kafka:9092} \
  -e GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT} \
  -e GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp/credentials.json \
  -v $(pwd)/config/gcp-credentials.json:/etc/gcp/credentials.json:ro \
  vertex-ai-service:latest

# Dispatch Service
docker run -d \
  --name dispatch-service \
  --network deployment_default \
  -p 8001:8001 \
  -e CONFLUENT_BOOTSTRAP_SERVERS=${CONFLUENT_BOOTSTRAP_SERVERS:-kafka:9092} \
  dispatch-service:latest

# Dashboard
docker run -d \
  --name dashboard \
  --network deployment_default \
  -p 3000:80 \
  dashboard:latest

# Simulators
docker run -d \
  --name order-simulator \
  --network deployment_default \
  -e CONFLUENT_BOOTSTRAP_SERVERS=${CONFLUENT_BOOTSTRAP_SERVERS:-kafka:9092} \
  order-simulator:latest

docker run -d \
  --name vehicle-simulator \
  --network deployment_default \
  -e CONFLUENT_BOOTSTRAP_SERVERS=${CONFLUENT_BOOTSTRAP_SERVERS:-kafka:9092} \
  vehicle-simulator:latest

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Dashboard: http://localhost:3000"
echo "  - Dispatch Center: http://localhost:8001"
echo "  - AI Service: http://localhost:8000"
echo ""
echo "View logs:"
echo "  docker logs -f vertex-ai-service"
echo "  docker logs -f dispatch-service"
echo ""
echo "Stop all:"
echo "  docker stop vertex-ai-service dispatch-service dashboard order-simulator vehicle-simulator"
echo "  docker-compose -f deployment/docker-compose.yml down"

