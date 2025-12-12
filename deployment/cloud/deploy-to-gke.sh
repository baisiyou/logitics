#!/bin/bash

# Complete GKE deployment script

set -e

echo "=========================================="
echo "Amazon Logistics System - GKE Deployment"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}
CLUSTER_NAME=${CLUSTER_NAME:-"logistics-cluster"}
ZONE=${ZONE:-"us-east1-a"}
REGION=${REGION:-"us-east1"}

echo "Configuration:"
echo "  Project: ${PROJECT_ID}"
echo "  Cluster: ${CLUSTER_NAME}"
echo "  Zone: ${ZONE}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found"
    echo "Installing gcloud..."
    ./deployment/cloud/install-gcloud-manual.sh
    echo "Please restart your terminal or run: source ~/.zshrc"
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Check if authenticated
echo "Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please authenticate with GCP..."
    gcloud auth login
fi

# Enable required APIs
echo "Enabling required GCP APIs..."
gcloud services enable \
    container.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    --quiet

# Check if cluster exists
echo "Checking if cluster exists..."
if gcloud container clusters describe ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
    echo "✅ Cluster ${CLUSTER_NAME} already exists"
    read -p "Use existing cluster? (y/n): " USE_EXISTING
    if [ "$USE_EXISTING" != "y" ]; then
        echo "Please delete the cluster first or choose a different name"
        exit 1
    fi
else
    echo "Creating GKE cluster..."
    gcloud container clusters create ${CLUSTER_NAME} \
        --zone=${ZONE} \
        --num-nodes=3 \
        --machine-type=n1-standard-2 \
        --enable-autoscaling \
        --min-nodes=2 \
        --max-nodes=5 \
        --enable-autorepair \
        --enable-autoupgrade \
        --project=${PROJECT_ID} \
        --quiet
    
    echo "✅ Cluster created successfully"
fi

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID}

# Verify kubectl connection
echo "Verifying Kubernetes connection..."
kubectl cluster-info

# Update image paths in k8s files
echo "Updating image paths..."
find deployment/cloud/k8s -name "*.yaml" -type f -exec sed -i '' "s/YOUR_PROJECT_ID/${PROJECT_ID}/g" {} \;

# Sync .env to Kubernetes configs
echo "Syncing .env to Kubernetes configs..."
./deployment/cloud/sync-env-to-k8s.sh .env

# Build and push images
echo ""
echo "=========================================="
echo "Building and pushing Docker images"
echo "=========================================="
read -p "Build and push Docker images? (y/n): " BUILD_IMAGES
if [ "$BUILD_IMAGES" = "y" ]; then
    ./deployment/cloud/build-and-push.sh
else
    echo "Skipping image build. Make sure images are already in GCR."
fi

# Create namespace
echo "Creating namespace..."
kubectl apply -f deployment/cloud/k8s/namespace.yaml

# Create secrets
echo "Creating secrets..."
kubectl apply -f deployment/cloud/k8s/secrets.yaml

# Create configmap
echo "Creating configmap..."
kubectl apply -f deployment/cloud/k8s/configmap.yaml

# Deploy services
echo ""
echo "=========================================="
echo "Deploying services"
echo "=========================================="

echo "Deploying Vertex AI service..."
kubectl apply -f deployment/cloud/k8s/vertex-ai-service.yaml

echo "Deploying Dispatch service..."
kubectl apply -f deployment/cloud/k8s/dispatch-service.yaml

echo "Deploying Driver service..."
kubectl apply -f deployment/cloud/k8s/driver-service.yaml

echo "Deploying Warehouse service..."
kubectl apply -f deployment/cloud/k8s/warehouse-service.yaml

echo "Deploying Customer service..."
kubectl apply -f deployment/cloud/k8s/customer-service.yaml

echo "Deploying Dashboard..."
kubectl apply -f deployment/cloud/k8s/dashboard-service.yaml

echo "Deploying Simulators..."
kubectl apply -f deployment/cloud/k8s/simulators.yaml

# Wait for deployments
echo ""
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/vertex-ai-service -n logistics-system || true
kubectl wait --for=condition=available --timeout=300s deployment/dispatch-service -n logistics-system || true
kubectl wait --for=condition=available --timeout=300s deployment/dashboard -n logistics-system || true

# Get service information
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Service Status:"
kubectl get services -n logistics-system

echo ""
echo "Pod Status:"
kubectl get pods -n logistics-system

echo ""
echo "Dashboard URL:"
DASHBOARD_IP=$(kubectl get service dashboard-service -n logistics-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "$DASHBOARD_IP" != "pending" ] && [ -n "$DASHBOARD_IP" ]; then
    echo "  http://${DASHBOARD_IP}"
else
    echo "  External IP is being provisioned..."
    echo "  Check with: kubectl get service dashboard-service -n logistics-system"
    echo ""
    echo "  Or use port-forward for local access:"
    echo "  kubectl port-forward service/dashboard-service 3000:80 -n logistics-system"
    echo "  Then open: http://localhost:3000"
fi

echo ""
echo "Useful commands:"
echo "  View logs: kubectl logs -f deployment/vertex-ai-service -n logistics-system"
echo "  View all: kubectl get all -n logistics-system"
echo "  Scale service: kubectl scale deployment vertex-ai-service --replicas=5 -n logistics-system"

