# Alternative Deployment Methods

If you don't have Google Cloud SDK installed or prefer other deployment methods, here are alternatives:

## Option 1: Docker Compose (Local/Any Server)

Deploy using Docker Compose without cloud account:

```bash
./deployment/cloud/deploy-docker-compose.sh
```

This will:
- Start Kafka, PostgreSQL, Redis using Docker Compose
- Build and run application containers
- No cloud account needed

## Option 2: Install Google Cloud SDK

### macOS

```bash
# Using Homebrew (recommended)
brew install --cask google-cloud-sdk

# Or manual install
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Linux

```bash
# Add Cloud SDK repository
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

# Import key
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

# Install
sudo apt-get update && sudo apt-get install google-cloud-sdk
```

### After Installation

```bash
# Initialize
gcloud init

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID
```

## Option 3: Use AWS EKS

1. Install AWS CLI and eksctl
2. Create EKS cluster
3. Build and push images to ECR
4. Deploy using kubectl (same k8s manifests)

## Option 4: Use Azure AKS

1. Install Azure CLI
2. Create AKS cluster
3. Build and push images to ACR
4. Deploy using kubectl

## Option 5: Use Managed Kubernetes Services

- **DigitalOcean Kubernetes**
- **Linode Kubernetes**
- **Vultr Kubernetes**

All support standard Kubernetes manifests.

## Quick Local Test

For quick local testing without cloud:

```bash
# Use existing local deployment
cd /Users/zrb/Documents/amazon
./deployment/deploy.sh
```

This uses Docker Compose and runs everything locally.

