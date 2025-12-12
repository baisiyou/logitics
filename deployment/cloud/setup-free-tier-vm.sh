#!/bin/bash

# Complete setup for GCP Free Tier VM deployment

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}
VM_NAME=${VM_NAME:-"logistics-vm"}
ZONE=${ZONE:-"us-east1-a"}

echo "=========================================="
echo "GCP Free Tier VM Setup"
echo "=========================================="
echo "Project: ${PROJECT_ID}"
echo "VM Name: ${VM_NAME}"
echo "Zone: ${ZONE}"
echo ""

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q .; then
    echo "⚠️  Not authenticated. Please login..."
    gcloud auth login
fi

gcloud config set project ${PROJECT_ID}

# Check billing
echo "Checking billing status..."
BILLING_ENABLED=$(gcloud billing projects describe ${PROJECT_ID} --format="value(billingAccountName)" 2>/dev/null || echo "")

if [ -z "$BILLING_ENABLED" ]; then
    echo ""
    echo "❌ Billing account not linked"
    echo ""
    echo "To use free tier VM, you need to:"
    echo "  1. Enable billing (required for API access)"
    echo "  2. Free tier gives you:"
    echo "     - 1 f1-micro VM/month (FREE)"
    echo "     - 30GB disk (FREE)"
    echo "     - 1GB network egress (FREE)"
    echo ""
    echo "📋 Steps to enable billing:"
    echo "  1. Visit: https://console.cloud.google.com/billing?project=${PROJECT_ID}"
    echo "  2. Create or link a billing account"
    echo "  3. Run this script again"
    echo ""
    echo "💡 Note: You won't be charged if you stay within free tier limits"
    echo ""
    read -p "Have you enabled billing? (y/n): " BILLING_DONE
    if [ "$BILLING_DONE" != "y" ]; then
        echo "Please enable billing first, then run this script again."
        exit 1
    fi
fi

# Enable APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable \
    compute.googleapis.com \
    --project=${PROJECT_ID} \
    --quiet

echo "✅ APIs enabled"

# Check if VM exists
echo ""
echo "Checking if VM exists..."
if gcloud compute instances describe ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
    echo "✅ VM ${VM_NAME} already exists"
    VM_IP=$(gcloud compute instances describe ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID} --format="get(networkInterfaces[0].accessConfigs[0].natIP)")
    echo "VM IP: ${VM_IP}"
else
    echo "Creating free tier VM (f1-micro)..."
    gcloud compute instances create ${VM_NAME} \
        --zone=${ZONE} \
        --machine-type=f1-micro \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=20GB \
        --boot-disk-type=pd-standard \
        --project=${PROJECT_ID} \
        --quiet
    
    echo "✅ VM created"
    echo "Waiting for VM to be ready..."
    sleep 30
    
    VM_IP=$(gcloud compute instances describe ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID} --format="get(networkInterfaces[0].accessConfigs[0].natIP)")
    echo "VM IP: ${VM_IP}"
fi

# Create deployment package
echo ""
echo "Preparing deployment package..."
DEPLOY_DIR="/tmp/logistics-deploy"
rm -rf ${DEPLOY_DIR}
mkdir -p ${DEPLOY_DIR}

# Copy necessary files
cp -r deployment ${DEPLOY_DIR}/
cp -r data-sources ${DEPLOY_DIR}/
cp -r confluent ${DEPLOY_DIR}/
cp -r ai-inference ${DEPLOY_DIR}/
cp -r applications ${DEPLOY_DIR}/
cp requirements.txt ${DEPLOY_DIR}/
cp .env ${DEPLOY_DIR}/ 2>/dev/null || echo "# Add your .env file" > ${DEPLOY_DIR}/.env

# Create deployment script for VM
cat > ${DEPLOY_DIR}/deploy-on-vm.sh <<'VMSCRIPT'
#!/bin/bash
set -e

echo "=========================================="
echo "Deploying on VM"
echo "=========================================="

# Update system
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3-pip git

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Install Python dependencies
pip3 install -r requirements.txt

# Start infrastructure
cd deployment
sudo docker-compose up -d

# Wait for services
sleep 30

# Create Kafka topics
cd ..
python3 scripts/create_topics.py

# Build and run application containers
sudo docker build -f deployment/cloud/Dockerfile.vertex-ai -t vertex-ai-service:latest .
sudo docker build -f deployment/cloud/Dockerfile.dispatch -t dispatch-service:latest .
sudo docker build -f deployment/cloud/Dockerfile.dashboard -t dashboard:latest .

# Run services
sudo docker run -d --name vertex-ai-service --network deployment_default -p 8000:8000 vertex-ai-service:latest
sudo docker run -d --name dispatch-service --network deployment_default -p 8001:8001 dispatch-service:latest
sudo docker run -d --name dashboard --network deployment_default -p 80:80 dashboard:latest

echo "✅ Deployment complete!"
echo "Services available at VM IP on ports 80, 8000, 8001"
VMSCRIPT

chmod +x ${DEPLOY_DIR}/deploy-on-vm.sh

# Copy to VM
echo ""
echo "Copying files to VM..."
gcloud compute scp --recurse ${DEPLOY_DIR}/* ${VM_NAME}:~/logistics-deploy --zone=${ZONE} --project=${PROJECT_ID}

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. SSH into VM:"
echo "   gcloud compute ssh ${VM_NAME} --zone=${ZONE}"
echo ""
echo "2. On the VM, run:"
echo "   cd ~/logistics-deploy"
echo "   ./deploy-on-vm.sh"
echo ""
echo "3. Access services:"
echo "   Dashboard: http://${VM_IP}"
echo "   Dispatch: http://${VM_IP}:8001"
echo "   AI Service: http://${VM_IP}:8000"
echo ""
echo "Note: Update firewall rules if needed:"
echo "   gcloud compute firewall-rules create allow-http --allow tcp:80,tcp:8000,tcp:8001 --source-ranges 0.0.0.0/0"

