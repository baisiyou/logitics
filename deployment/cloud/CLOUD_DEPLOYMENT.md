# Cloud Deployment Guide

This guide covers deploying the Amazon Logistics Intelligent Dispatch System to cloud platforms.

## Supported Platforms

- **Google Cloud Platform (GCP)** - Recommended
- **Amazon Web Services (AWS)**
- **Microsoft Azure**

## Prerequisites

1. **Cloud Account Setup**
   - GCP: Create project and enable billing
   - AWS: Create account and configure IAM
   - Azure: Create subscription and resource group

2. **Required Tools**
   ```bash
   # Install Google Cloud SDK
   curl https://sdk.cloud.google.com | bash
   
   # Install kubectl
   gcloud components install kubectl
   
   # Install Docker
   # Follow platform-specific instructions
   ```

3. **Kubernetes Cluster**
   - GCP: Create GKE cluster
   - AWS: Create EKS cluster
   - Azure: Create AKS cluster

## GCP Deployment (Recommended)

### 1. Setup GCP Project

```bash
# Set project
export GOOGLE_CLOUD_PROJECT=your-project-id
gcloud config set project ${GOOGLE_CLOUD_PROJECT}

# Enable required APIs
gcloud services enable \
  container.googleapis.com \
  containerregistry.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com
```

### 2. Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create logistics-cluster \
  --zone=us-central1-a \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=5

# Get credentials
gcloud container clusters get-credentials logistics-cluster --zone=us-central1-a
```

### 3. Setup Confluent Cloud

1. Sign up for Confluent Cloud
2. Create a cluster
3. Get bootstrap servers and API keys
4. Update `k8s/configmap.yaml` and `k8s/secrets.yaml`

### 4. Build and Push Docker Images

```bash
# Authenticate
gcloud auth configure-docker

# Build and push
chmod +x deployment/cloud/build-and-push.sh
./deployment/cloud/build-and-push.sh
```

### 5. Configure Secrets

Edit `deployment/cloud/k8s/secrets.yaml`:

```yaml
stringData:
  CONFLUENT_API_KEY: "your-actual-api-key"
  CONFLUENT_API_SECRET: "your-actual-api-secret"
  GOOGLE_CLOUD_PROJECT: "your-project-id"
  POSTGRES_PASSWORD: "your-secure-password"
  # ... other secrets
```

### 6. Deploy to GKE

```bash
chmod +x deployment/cloud/deploy-gcp.sh
./deployment/cloud/deploy-gcp.sh
```

### 7. Access Services

```bash
# Get dashboard URL
kubectl get service dashboard-service -n logistics-system

# Port forward for local access
kubectl port-forward service/dashboard-service 3000:80 -n logistics-system
```

## AWS Deployment

### 1. Setup EKS Cluster

```bash
# Install eksctl
brew install eksctl

# Create cluster
eksctl create cluster \
  --name logistics-cluster \
  --region us-east-1 \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5
```

### 2. Build and Push to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repositories
aws ecr create-repository --repository-name vertex-ai-service
aws ecr create-repository --repository-name dispatch-service
aws ecr create-repository --repository-name dashboard

# Build and push (modify build script for ECR)
```

### 3. Deploy to EKS

```bash
# Update image paths in k8s yaml files
# Then apply
kubectl apply -f deployment/cloud/k8s/
```

## Azure Deployment

### 1. Setup AKS Cluster

```bash
# Login
az login

# Create resource group
az group create --name logistics-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group logistics-rg \
  --name logistics-cluster \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group logistics-rg --name logistics-cluster
```

### 2. Build and Push to ACR

```bash
# Login to ACR
az acr login --name YOUR_REGISTRY_NAME

# Build and push
az acr build --registry YOUR_REGISTRY_NAME --image vertex-ai-service:latest .
```

## Environment Variables

### Required Variables

- `CONFLUENT_BOOTSTRAP_SERVERS` - Kafka bootstrap servers
- `CONFLUENT_API_KEY` - Confluent API key
- `CONFLUENT_API_SECRET` - Confluent API secret
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account JSON

### Optional Variables

- `VERTEX_AI_LOCATION` - Default: us-central1
- `BIGQUERY_DATASET` - Default: logistics_analytics
- `POSTGRES_HOST` - Database host
- `REDIS_HOST` - Redis host

## Monitoring and Logging

### GCP

```bash
# View logs
gcloud logging read "resource.type=k8s_container" --limit 50

# View metrics
# Use Cloud Monitoring dashboard
```

### Kubernetes

```bash
# View pod logs
kubectl logs -f deployment/vertex-ai-service -n logistics-system

# View all resources
kubectl get all -n logistics-system

# Describe service
kubectl describe service dispatch-service -n logistics-system
```

## Scaling

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment vertex-ai-service --replicas=5 -n logistics-system
```

### Auto Scaling

```bash
# Create HPA
kubectl autoscale deployment vertex-ai-service \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n logistics-system
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n logistics-system

# Describe pod
kubectl describe pod POD_NAME -n logistics-system

# View logs
kubectl logs POD_NAME -n logistics-system
```

### Services not accessible

```bash
# Check service endpoints
kubectl get endpoints -n logistics-system

# Check ingress
kubectl get ingress -n logistics-system
```

### Image pull errors

```bash
# Check image pull secrets
kubectl get secrets -n logistics-system

# Verify image exists
gcloud container images list-tags gcr.io/PROJECT_ID/vertex-ai-service
```

## Cost Optimization

1. **Use preemptible nodes** (GCP)
2. **Right-size instances**
3. **Enable cluster autoscaling**
4. **Use managed services** (Cloud SQL, Memorystore)
5. **Monitor resource usage**

## Security Best Practices

1. **Use secrets management** (GCP Secret Manager, AWS Secrets Manager)
2. **Enable network policies**
3. **Use private clusters**
4. **Enable audit logging**
5. **Regular security updates**

## Next Steps

- Set up CI/CD pipeline
- Configure monitoring and alerting
- Implement backup strategies
- Set up disaster recovery

