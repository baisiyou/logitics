#!/bin/bash

# Quick start script for GCP deployment

set -e

echo "=========================================="
echo "Amazon Logistics System - GCP Quick Start"
echo "=========================================="

# Check prerequisites
command -v gcloud >/dev/null 2>&1 || { echo "Error: gcloud CLI not found. Please install Google Cloud SDK."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl not found. Please install kubectl."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Error: docker not found. Please install Docker."; exit 1; }

# Get project ID
read -p "Enter your GCP Project ID: " PROJECT_ID
export GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
gcloud config set project ${PROJECT_ID}

# Enable APIs
echo "Enabling required APIs..."
gcloud services enable \
  container.googleapis.com \
  containerregistry.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  --quiet

# Create GKE cluster
read -p "Create new GKE cluster? (y/n): " CREATE_CLUSTER
if [ "$CREATE_CLUSTER" = "y" ]; then
  read -p "Cluster name (default: logistics-cluster): " CLUSTER_NAME
  CLUSTER_NAME=${CLUSTER_NAME:-logistics-cluster}
  
  read -p "Zone (default: us-central1-a): " ZONE
  ZONE=${ZONE:-us-central1-a}
  
  echo "Creating GKE cluster..."
  gcloud container clusters create ${CLUSTER_NAME} \
    --zone=${ZONE} \
    --num-nodes=3 \
    --machine-type=n1-standard-2 \
    --enable-autoscaling \
    --min-nodes=2 \
    --max-nodes=5 \
    --quiet
  
  export CLUSTER_NAME=${CLUSTER_NAME}
  export ZONE=${ZONE}
else
  read -p "Existing cluster name: " CLUSTER_NAME
  read -p "Zone: " ZONE
  export CLUSTER_NAME=${CLUSTER_NAME}
  export ZONE=${ZONE}
fi

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE}

# Update image paths in k8s files
echo "Updating image paths..."
find deployment/cloud/k8s -name "*.yaml" -exec sed -i '' "s/YOUR_PROJECT_ID/${PROJECT_ID}/g" {} \;

# Build and push images
read -p "Build and push Docker images? (y/n): " BUILD_IMAGES
if [ "$BUILD_IMAGES" = "y" ]; then
  ./deployment/cloud/build-and-push.sh
fi

# Configure secrets
echo ""
echo "=========================================="
echo "Please update secrets in deployment/cloud/k8s/secrets.yaml"
echo "Required secrets:"
echo "  - CONFLUENT_API_KEY"
echo "  - CONFLUENT_API_SECRET"
echo "  - POSTGRES_PASSWORD"
echo "  - GOOGLE_APPLICATION_CREDENTIALS (base64 encoded)"
echo "=========================================="
read -p "Press Enter after updating secrets..."

# Deploy
echo "Deploying to GKE..."
./deployment/cloud/deploy-gcp.sh

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Get service URLs:"
echo "  kubectl get services -n logistics-system"
echo ""
echo "Access dashboard:"
echo "  kubectl port-forward service/dashboard-service 3000:80 -n logistics-system"
echo "  Then open http://localhost:3000"

