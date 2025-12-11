#!/bin/bash

# Deploy to Google Cloud Platform (GKE)

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
CLUSTER_NAME=${CLUSTER_NAME:-"logistics-cluster"}
ZONE=${ZONE:-"us-central1-a"}
NAMESPACE="logistics-system"

echo "=========================================="
echo "Deploying to Google Cloud Platform"
echo "Project: ${PROJECT_ID}"
echo "Cluster: ${CLUSTER_NAME}"
echo "=========================================="

# Set project
gcloud config set project ${PROJECT_ID}

# Get cluster credentials
echo "Getting cluster credentials..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${ZONE}

# Create namespace
echo "Creating namespace..."
kubectl apply -f deployment/cloud/k8s/namespace.yaml

# Create secrets (update with your values first)
echo "Creating secrets..."
kubectl apply -f deployment/cloud/k8s/secrets.yaml

# Create configmap
echo "Creating configmap..."
kubectl apply -f deployment/cloud/k8s/configmap.yaml

# Deploy services
echo "Deploying services..."
kubectl apply -f deployment/cloud/k8s/vertex-ai-service.yaml
kubectl apply -f deployment/cloud/k8s/dispatch-service.yaml
kubectl apply -f deployment/cloud/k8s/dashboard-service.yaml
kubectl apply -f deployment/cloud/k8s/simulators.yaml

# Wait for deployments
echo "Waiting for deployments..."
kubectl wait --for=condition=available --timeout=300s deployment/vertex-ai-service -n ${NAMESPACE}
kubectl wait --for=condition=available --timeout=300s deployment/dispatch-service -n ${NAMESPACE}
kubectl wait --for=condition=available --timeout=300s deployment/dashboard -n ${NAMESPACE}

# Get service URLs
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Service URLs:"
kubectl get services -n ${NAMESPACE}

echo ""
echo "Dashboard URL:"
kubectl get service dashboard-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

echo ""
echo "To view logs:"
echo "  kubectl logs -f deployment/vertex-ai-service -n ${NAMESPACE}"
echo "  kubectl logs -f deployment/dispatch-service -n ${NAMESPACE}"

