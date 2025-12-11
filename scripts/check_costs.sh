#!/bin/bash

# Check costs for Amazon Logistics System

set -e

export PATH="$HOME/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"baisiyou"}

echo "=========================================="
echo "费用检查 - Amazon Logistics System"
echo "=========================================="
echo ""

# Check GCP Billing
echo "1. Google Cloud Platform (GCP) 费用"
echo "----------------------------------------"
BILLING_ACCOUNT=$(gcloud billing projects describe ${PROJECT_ID} --format="value(billingAccountName)" 2>/dev/null || echo "")

if [ -z "$BILLING_ACCOUNT" ]; then
    echo "   ✅ 计费账户未启用"
    echo "   💰 费用: \$0 (不会产生费用)"
    echo "   ⚠️  注意: 无法使用需要计费的 GCP 服务"
else
    echo "   ⚠️  计费账户已启用: ${BILLING_ACCOUNT}"
    echo "   📊 查看费用: https://console.cloud.google.com/billing?project=${PROJECT_ID}"
    echo ""
    echo "   当前启用的服务:"
    gcloud services list --enabled --project=${PROJECT_ID} 2>/dev/null | grep -E "(aiplatform|compute|bigquery|container)" | awk '{print "      - " $1}' || echo "      无需要计费的服务"
fi

echo ""
echo "2. Confluent Cloud 费用"
echo "----------------------------------------"
if [ -f .env ]; then
    CONFLUENT_SERVERS=$(grep CONFLUENT_BOOTSTRAP_SERVERS .env | cut -d'=' -f2 | grep -v localhost | grep -v "^$" || echo "")
    if [ -n "$CONFLUENT_SERVERS" ]; then
        echo "   ⚠️  使用 Confluent Cloud"
        echo "   📊 查看费用: https://confluent.cloud/"
        echo "   💰 费用取决于:"
        echo "      - 数据吞吐量"
        echo "      - 存储使用量"
        echo "      - 连接数"
    else
        echo "   ✅ 使用本地 Kafka (Docker)"
        echo "   💰 费用: \$0"
    fi
else
    echo "   ⚠️  无法检查 .env 文件"
fi

echo ""
echo "3. 当前运行的服务"
echo "----------------------------------------"
echo "   本地服务 (免费):"
LOCAL_SERVICES=$(ps aux | grep -E "(vertex_ai|dispatch|driver|warehouse|customer|simulator)" | grep python3 | grep -v grep | wc -l | tr -d ' ')
echo "      - Python 服务: ${LOCAL_SERVICES} 个"
echo "      - Docker 服务: $(docker ps 2>/dev/null | wc -l | tr -d ' ') 个容器"
echo "   💰 费用: \$0 (本地运行)"

echo ""
echo "4. 费用估算"
echo "----------------------------------------"
echo "   当前配置的费用:"
echo ""
echo "   ✅ 本地运行: \$0"
echo "      - 所有服务在本地运行"
echo "      - 使用本地 Docker Kafka"
echo ""
if [ -n "$BILLING_ACCOUNT" ]; then
    echo "   ⚠️  GCP 服务 (如果使用):"
    echo "      - Vertex AI API: ~\$0.001-0.01/次调用"
    echo "      - BigQuery: ~\$5/TB 查询"
    echo "      - Compute Engine (如果创建 VM): ~\$5-50/月"
    echo ""
fi
if [ -n "$CONFLUENT_SERVERS" ]; then
    echo "   ⚠️  Confluent Cloud:"
    echo "      - Basic 计划: ~\$1/小时"
    echo "      - Standard 计划: ~\$3-5/小时"
    echo "      - 查看实际费用: https://confluent.cloud/billing"
    echo ""
fi

echo ""
echo "=========================================="
echo "费用检查链接"
echo "=========================================="
echo ""
echo "GCP 费用:"
echo "  https://console.cloud.google.com/billing?project=${PROJECT_ID}"
echo ""
echo "Confluent Cloud 费用:"
echo "  https://confluent.cloud/billing"
echo ""
echo "GCP 使用情况:"
echo "  https://console.cloud.google.com/apis/dashboard?project=${PROJECT_ID}"
echo ""

