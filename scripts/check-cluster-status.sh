#!/bin/bash

# Check GKE cluster status

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

CLUSTER_NAME=${CLUSTER_NAME:-"logistics-cluster"}
ZONE=${ZONE:-"us-central1-a"}
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}

echo "=========================================="
echo "检查 GKE 集群状态"
echo "=========================================="
echo "集群: ${CLUSTER_NAME}"
echo "区域: ${ZONE}"
echo "项目: ${PROJECT_ID}"
echo ""

# Get cluster status
STATUS=$(gcloud container clusters describe ${CLUSTER_NAME} \
    --zone=${ZONE} \
    --project=${PROJECT_ID} \
    --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$STATUS" = "NOT_FOUND" ]; then
    echo "❌ 集群不存在"
    exit 1
fi

echo "状态: ${STATUS}"
echo ""

case $STATUS in
    "PROVISIONING")
        echo "⏳ 集群正在创建中..."
        echo "   通常需要 5-10 分钟"
        echo "   请稍候..."
        ;;
    "RUNNING")
        echo "✅ 集群运行中！"
        echo ""
        echo "获取凭证:"
        echo "  gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID}"
        echo ""
        echo "部署应用:"
        echo "  ./deployment/cloud/deploy-to-gke.sh"
        ;;
    "RECONCILING")
        echo "🔄 集群正在更新中..."
        ;;
    "STOPPING")
        echo "⏹️  集群正在停止..."
        ;;
    "ERROR")
        echo "❌ 集群创建失败"
        echo "查看错误:"
        gcloud container clusters describe ${CLUSTER_NAME} --zone=${ZONE} --project=${PROJECT_ID} --format="value(conditions)"
        ;;
    *)
        echo "状态: ${STATUS}"
        ;;
esac

echo ""
echo "详细信息:"
gcloud container clusters describe ${CLUSTER_NAME} \
    --zone=${ZONE} \
    --project=${PROJECT_ID} \
    --format="table(
        name,
        location,
        status,
        currentNodeCount,
        targetNodeCount,
        endpoint
    )"

