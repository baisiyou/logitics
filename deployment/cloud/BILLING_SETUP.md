# GCP Billing Setup Guide

## Issue

Your GCP project needs billing enabled to use GKE and other services.

Error: `Billing account for project '76270195660' is not found`

## Solution Options

### Option 1: Enable Billing for GKE (Recommended for Production)

**Steps:**

1. **Go to GCP Console Billing**
   ```
   https://console.cloud.google.com/billing?project=baisiyou
   ```

2. **Create or Link Billing Account**
   - If you have a billing account: Link it to project 'baisiyou'
   - If not: Create a new billing account (requires credit card)

3. **Verify Billing is Enabled**
   ```bash
   gcloud billing accounts list
   gcloud billing projects link baisiyou --billing-account=BILLING_ACCOUNT_ID
   ```

4. **Retry Deployment**
   ```bash
   ./deployment/cloud/quick-deploy.sh
   ```

**Cost:** ~$150-300/month for GKE cluster

---

### Option 2: Use Docker Compose on VPS (No GCP Billing)

Deploy to any VPS provider (DigitalOcean, Linode, Vultr, etc.)

**Steps:**

1. **Get a VPS** (~$20-50/month)
   - 4-8GB RAM
   - 2-4 vCPU
   - Ubuntu 20.04+

2. **Deploy**
   ```bash
   # On your VPS
   git clone <your-repo>
   cd amazon
   ./deployment/cloud/deploy-docker-compose.sh
   ```

**Cost:** ~$20-50/month (VPS only)

---

### Option 3: Use GCP Compute Engine Free Tier

GKE doesn't have free tier, but you can use Compute Engine.

**Steps:**

1. **Create a small VM** (f1-micro is free tier eligible)
   ```bash
   gcloud compute instances create logistics-vm \
     --zone=us-east1-a \
     --machine-type=f1-micro \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --project=baisiyou
   ```

2. **SSH into VM and deploy**
   ```bash
   gcloud compute ssh logistics-vm --zone=us-east1-a
   # Then run Docker Compose deployment
   ```

**Cost:** Free (within free tier limits)

---

### Option 4: Use Other Cloud Providers

- **AWS EKS**: Similar to GKE
- **Azure AKS**: Similar to GKE
- **DigitalOcean Kubernetes**: Simpler, cheaper
- **Linode Kubernetes**: Budget-friendly

---

## Quick Fix Commands

### Check Billing Status
```bash
gcloud billing projects describe baisiyou
```

### Link Billing Account
```bash
# List billing accounts
gcloud billing accounts list

# Link to project
gcloud billing projects link baisiyou --billing-account=BILLING_ACCOUNT_ID
```

### Alternative: Deploy with Docker Compose
```bash
# No billing needed
./deployment/cloud/deploy-docker-compose.sh
```

## Recommendation

**If you want production-grade infrastructure:**
- Enable billing and use GKE
- Cost: ~$150-300/month

**If you want to save money:**
- Use Docker Compose on VPS
- Cost: ~$20-50/month

**If you want to test for free:**
- Use GCP Compute Engine free tier
- Deploy with Docker Compose
- Cost: $0 (within limits)

