#!/bin/bash

# Fix GKE cluster creation permissions

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}

echo "=========================================="
echo "修复 GKE 权限问题"
echo "=========================================="
echo "项目: ${PROJECT_ID}"
echo ""

# Check billing
echo "1. 检查计费账户..."
BILLING_ACCOUNT=$(gcloud billing projects describe ${PROJECT_ID} --format="value(billingAccountName)" 2>/dev/null || echo "")

if [ -z "$BILLING_ACCOUNT" ]; then
    echo "   ❌ 计费账户未启用"
    echo ""
    echo "   GKE 需要启用计费账户才能创建集群"
    echo "   请访问: https://console.cloud.google.com/billing?project=${PROJECT_ID}"
    echo "   创建或关联计费账户"
    echo ""
    read -p "   已启用计费账户？(y/n): " BILLING_DONE
    if [ "$BILLING_DONE" != "y" ]; then
        echo "   请先启用计费账户，然后重新运行此脚本"
        exit 1
    fi
else
    echo "   ✅ 计费账户: ${BILLING_ACCOUNT}"
fi

# Enable APIs
echo ""
echo "2. 启用必需的 API..."
gcloud services enable \
    container.googleapis.com \
    compute.googleapis.com \
    --project=${PROJECT_ID} \
    --quiet

echo "   ✅ API 已启用"

# Check permissions
echo ""
echo "3. 检查权限..."
USER_EMAIL=$(gcloud config get-value account)

echo "   当前用户: ${USER_EMAIL}"
echo ""
echo "   需要的权限:"
echo "   - roles/container.admin (GKE 管理)"
echo "   - roles/compute.admin (计算引擎管理)"
echo "   - roles/iam.serviceAccountUser (服务账户使用)"
echo ""

# Try to grant permissions (if user is project owner)
echo "4. 尝试授予权限..."
echo "   注意: 只有项目所有者可以授予权限"
echo ""

# Check if user is owner
IS_OWNER=$(gcloud projects get-iam-policy ${PROJECT_ID} \
    --flatten="bindings[].members" \
    --filter="bindings.members:user:${USER_EMAIL} AND bindings.role:roles/owner" \
    --format="value(bindings.role)" 2>/dev/null | grep -q owner && echo "yes" || echo "no")

if [ "$IS_OWNER" = "yes" ]; then
    echo "   ✅ 您是项目所有者，可以授予权限"
    echo ""
    read -p "   是否授予 GKE 管理权限？(y/n): " GRANT_PERM
    if [ "$GRANT_PERM" = "y" ]; then
        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="user:${USER_EMAIL}" \
            --role="roles/container.admin" \
            --quiet
        
        gcloud projects add-iam-policy-binding ${PROJECT_ID} \
            --member="user:${USER_EMAIL}" \
            --role="roles/compute.admin" \
            --quiet
        
        echo "   ✅ 权限已授予"
    fi
else
    echo "   ⚠️  您不是项目所有者"
    echo "   请项目所有者运行以下命令授予权限:"
    echo ""
    echo "   gcloud projects add-iam-policy-binding ${PROJECT_ID} \\"
    echo "       --member=\"user:${USER_EMAIL}\" \\"
    echo "       --role=\"roles/container.admin\""
    echo ""
    echo "   gcloud projects add-iam-policy-binding ${PROJECT_ID} \\"
    echo "       --member=\"user:${USER_EMAIL}\" \\"
    echo "       --role=\"roles/compute.admin\""
fi

# Check available zones
echo ""
echo "5. 检查可用区域..."
ZONES=$(gcloud compute zones list --project=${PROJECT_ID} --filter="region:us-east1" --format="value(name)" 2>/dev/null | head -3)

if [ -n "$ZONES" ]; then
    echo "   可用区域:"
    echo "$ZONES" | while read zone; do
        echo "   - $zone"
    done
else
    echo "   ⚠️  无法列出区域（可能需要启用计费）"
    echo "   建议使用: us-central1-a (通常可用)"
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "如果问题仍然存在，请检查:"
echo "  1. 计费账户已启用: https://console.cloud.google.com/billing?project=${PROJECT_ID}"
echo "  2. 您有项目所有者或编辑者权限"
echo "  3. 等待几分钟让权限生效"
echo ""
echo "然后重试创建集群:"
echo "  gcloud container clusters create logistics-cluster \\"
echo "    --zone=us-central1-a \\"
echo "    --num-nodes=3 \\"
echo "    --machine-type=n1-standard-2 \\"
echo "    --project=${PROJECT_ID}"

