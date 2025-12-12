#!/bin/bash

# Create GKE cluster with alternative zones

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}
CLUSTER_NAME=${CLUSTER_NAME:-"logistics-cluster"}

echo "=========================================="
echo "创建 GKE 集群 (使用替代区域)"
echo "=========================================="
echo "项目: ${PROJECT_ID}"
echo "集群名: ${CLUSTER_NAME}"
echo ""

# Try different zones
ZONES=("us-central1-a" "us-central1-b" "us-west1-a" "us-east1-b" "us-east1-c")

for ZONE in "${ZONES[@]}"; do
    echo "尝试区域: ${ZONE}"
    
    # Check if cluster already exists
    if gcloud container clusters describe ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID} &>/dev/null; then
        echo "   ⚠️  集群已存在"
        continue
    fi
    
    # Try to create cluster
    if gcloud container clusters create ${CLUSTER_NAME} \
        --zone=${ZONE} \
        --num-nodes=3 \
        --machine-type=n1-standard-2 \
        --enable-autoscaling \
        --min-nodes=2 \
        --max-nodes=5 \
        --enable-autorepair \
        --enable-autoupgrade \
        --project=${PROJECT_ID} \
        --quiet 2>&1; then
        echo "   ✅ 集群创建成功！"
        echo ""
        echo "获取凭证:"
        echo "  gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID}"
        exit 0
    else
        echo "   ❌ 区域 ${ZONE} 不可用，尝试下一个..."
        continue
    fi
done

echo ""
echo "❌ 所有区域都不可用"
echo ""
echo "可能的原因:"
echo "  1. 需要等待几分钟让权限生效"
echo "  2. 区域配额不足"
echo "  3. 需要启用更多 API"
echo ""
echo "建议:"
echo "  1. 等待 10 分钟后重试"
echo "  2. 检查配额: https://console.cloud.google.com/iam-admin/quotas?project=${PROJECT_ID}"
echo "  3. 使用 Docker Compose: ./deployment/cloud/deploy-docker-compose.sh"

