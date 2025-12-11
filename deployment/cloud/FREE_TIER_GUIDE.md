# GCP Free Tier VM Deployment Guide

## Important Note

Even though you're using **free tier**, GCP requires a **billing account to be linked** to enable APIs. However:
- ✅ You won't be charged if you stay within free tier limits
- ✅ Free tier includes: 1 f1-micro VM, 30GB disk, 1GB egress per month
- ✅ Only pay if you exceed free tier

## Step-by-Step Setup

### Step 1: Enable Billing Account

1. **Visit GCP Console:**
   ```
   https://console.cloud.google.com/billing?project=baisiyou
   ```

2. **Create or Link Billing Account:**
   - If you have a billing account: Click "Link billing account"
   - If not: Click "Create billing account" (requires credit card)
   - Link it to project "baisiyou"

3. **Verify:**
   ```bash
   gcloud billing projects describe baisiyou
   ```

### Step 2: Run Setup Script

```bash
./deployment/cloud/setup-free-tier-vm.sh
```

This will:
- Enable Compute Engine API
- Create f1-micro VM (free tier)
- Copy deployment files to VM
- Provide instructions for deployment

### Step 3: Deploy on VM

```bash
# SSH into VM
gcloud compute ssh logistics-vm --zone=us-east1-a

# On the VM
cd ~/logistics-deploy
./deploy-on-vm.sh
```

### Step 4: Configure Firewall

Allow HTTP traffic:

```bash
gcloud compute firewall-rules create allow-logistics \
  --allow tcp:80,tcp:8000,tcp:8001 \
  --source-ranges 0.0.0.0/0 \
  --project=baisiyou
```

### Step 5: Access Services

- Dashboard: `http://VM_IP`
- Dispatch: `http://VM_IP:8001`
- AI Service: `http://VM_IP:8000`

## Free Tier Limits

- **1 f1-micro VM** per month (FREE)
- **30GB standard persistent disk** (FREE)
- **1GB network egress** to North America (FREE)
- **5GB network egress** to other regions (FREE)

## Cost Monitoring

Monitor usage to stay within free tier:

```bash
# Check VM usage
gcloud compute instances describe logistics-vm --zone=us-east1-a

# View billing
https://console.cloud.google.com/billing
```

## Troubleshooting

### VM creation fails
- Ensure billing is enabled
- Wait a few minutes after enabling billing
- Check API is enabled: `gcloud services list --enabled`

### Can't SSH
- Check firewall rules
- Verify VM is running: `gcloud compute instances list`

### Services not accessible
- Check firewall rules allow traffic
- Verify services are running: `sudo docker ps`
- Check logs: `sudo docker logs <container-name>`

## Alternative: No Billing Required

If you don't want to enable billing, use:
- **Local Docker deployment**: `./deployment/cloud/deploy-local-docker.sh`
- **External VPS**: DigitalOcean, Linode (~$5-10/month)

