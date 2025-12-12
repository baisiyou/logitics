# Cloud Deployment - Quick Start

## Overview

This directory contains all files needed to deploy the Amazon Logistics Intelligent Dispatch System to cloud platforms.

## Files Structure

```
deployment/cloud/
├── Dockerfile.*              # Docker images for each service
├── k8s/                      # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── vertex-ai-service.yaml
│   ├── dispatch-service.yaml
│   ├── dashboard-service.yaml
│   ├── driver-service.yaml
│   ├── warehouse-service.yaml
│   ├── customer-service.yaml
│   └── simulators.yaml
├── build-and-push.sh         # Build and push Docker images
├── deploy-gcp.sh             # Deploy to GKE
├── quick-start-gcp.sh        # Interactive quick start
├── CLOUD_DEPLOYMENT.md       # Detailed deployment guide
└── nginx.conf                # Nginx config for dashboard
```

## Quick Start (GCP)

### 1. Prerequisites

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Install kubectl
gcloud components install kubectl

# Authenticate
gcloud auth login
```

### 2. One-Command Setup

```bash
./deployment/cloud/quick-start-gcp.sh
```

This interactive script will:
- Enable required GCP APIs
- Create GKE cluster (optional)
- Build and push Docker images
- Deploy to Kubernetes

### 3. Manual Steps

#### Step 1: Set up GCP Project

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
gcloud config set project ${GOOGLE_CLOUD_PROJECT}
```

#### Step 2: Create GKE Cluster

```bash
gcloud container clusters create logistics-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=n1-standard-2
```

#### Step 3: Configure Secrets

Edit `k8s/secrets.yaml` with your actual values:
- Confluent Cloud API keys
- GCP service account credentials
- Database passwords

#### Step 4: Build and Push Images

```bash
./deployment/cloud/build-and-push.sh
```

#### Step 5: Deploy

```bash
./deployment/cloud/deploy-gcp.sh
```

## Access Services

```bash
# Get dashboard URL
kubectl get service dashboard-service -n logistics-system

# Port forward for local access
kubectl port-forward service/dashboard-service 3000:80 -n logistics-system
```

Then open http://localhost:3000

## Monitoring

```bash
# View all pods
kubectl get pods -n logistics-system

# View logs
kubectl logs -f deployment/vertex-ai-service -n logistics-system

# View service status
kubectl get services -n logistics-system
```

## Scaling

```bash
# Scale a service
kubectl scale deployment vertex-ai-service --replicas=5 -n logistics-system

# Auto-scaling
kubectl autoscale deployment vertex-ai-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n logistics-system
```

## Troubleshooting

See [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md) for detailed troubleshooting guide.

