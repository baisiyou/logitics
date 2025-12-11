#!/bin/bash

# Deploy to GCP Compute Engine VM (free tier eligible)

set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}
VM_NAME=${VM_NAME:-"logistics-vm"}
ZONE=${ZONE:-"us-east1-a"}

echo "=========================================="
echo "Deploying to GCP Compute Engine VM"
echo "=========================================="
echo "Project: ${PROJECT_ID}"
echo "VM Name: ${VM_NAME}"
echo "Zone: ${ZONE}"
echo ""

# Check if VM exists
if gcloud compute instances describe ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
    echo "✅ VM ${VM_NAME} already exists"
else
    echo "Creating VM..."
    gcloud compute instances create ${VM_NAME} \
        --zone=${ZONE} \
        --machine-type=f1-micro \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=20GB \
        --project=${PROJECT_ID} \
        --quiet
    
    echo "✅ VM created"
    echo "Waiting for VM to be ready..."
    sleep 30
fi

# Get VM IP
VM_IP=$(gcloud compute instances describe ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID} --format="get(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "VM IP: ${VM_IP}"
echo ""
echo "To deploy:"
echo "  1. SSH into VM:"
echo "     gcloud compute ssh ${VM_NAME} --zone=${ZONE}"
echo ""
echo "  2. On the VM, run:"
echo "     git clone <your-repo>"
echo "     cd amazon"
echo "     ./deployment/cloud/deploy-docker-compose.sh"
echo ""
echo "Or use this one-liner:"
echo "  gcloud compute ssh ${VM_NAME} --zone=${ZONE} --command='curl -sSL https://raw.githubusercontent.com/your-repo/deploy.sh | bash'"

