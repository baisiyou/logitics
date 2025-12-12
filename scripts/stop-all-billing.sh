#!/bin/bash

# Stop all billing - delete GKE cluster and check other services

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}

echo "=========================================="
echo "停止所有计费服务"
echo "=========================================="
echo ""

# Delete GKE clusters
echo "1. 删除 GKE 集群..."
CLUSTERS=$(gcloud container clusters list --project=${PROJECT_ID} --format="value(name,location)" 2>/dev/null || echo "")

if [ -n "$CLUSTERS" ]; then
    echo "$CLUSTERS" | while read name location; do
        ZONE=$(echo $location | cut -d'-' -f1-2)
        echo "  删除集群: $name (区域: $ZONE)"
        gcloud container clusters delete $name --zone=$ZONE --project=${PROJECT_ID} --quiet 2>/dev/null || true
    done
    echo "  ✅ GKE 集群已删除"
else
    echo "  ✅ 无 GKE 集群"
fi

# Check Compute Engine instances
echo ""
echo "2. 检查 Compute Engine 实例..."
VMS=$(gcloud compute instances list --project=${PROJECT_ID} --format="value(name,zone)" 2>/dev/null || echo "")

if [ -n "$VMS" ]; then
    echo "  发现以下 VM 实例:"
    echo "$VMS" | while read name zone; do
        echo "    - $name ($zone)"
    done
    echo ""
    read -p "  是否删除所有 VM 实例？(y/n): " DELETE_VMS
    if [ "$DELETE_VMS" = "y" ]; then
        echo "$VMS" | while read name zone; do
            echo "    删除: $name"
            gcloud compute instances delete $name --zone=$zone --project=${PROJECT_ID} --quiet 2>/dev/null || true
        done
        echo "  ✅ VM 实例已删除"
    fi
else
    echo "  ✅ 无 VM 实例"
fi

# Check other resources
echo ""
echo "3. 检查其他资源..."
echo "  - Cloud Storage buckets"
echo "  - BigQuery datasets"
echo "  - Cloud SQL instances"
echo ""
echo "  如需删除，请访问: https://console.cloud.google.com/?project=${PROJECT_ID}"

echo ""
echo "=========================================="
echo "费用检查"
echo "=========================================="
echo ""
echo "GCP 费用:"
echo "  https://console.cloud.google.com/billing?project=${PROJECT_ID}"
echo ""
echo "Confluent Cloud 费用:"
echo "  https://confluent.cloud/billing"
echo ""
echo "运行费用检查:"
echo "  ./scripts/check_costs.sh"

