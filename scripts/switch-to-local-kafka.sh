#!/bin/bash

# Switch to local Kafka (stop Confluent Cloud billing)

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "切换到本地 Kafka"
echo "=========================================="
echo ""

# Backup .env
if [ -f .env ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo "✅ 已备份 .env 文件"
fi

# Update .env
echo "更新 .env 配置..."
sed -i '' 's|^CONFLUENT_BOOTSTRAP_SERVERS=.*|CONFLUENT_BOOTSTRAP_SERVERS=localhost:9092|' .env
sed -i '' 's|^CONFLUENT_SCHEMA_REGISTRY_URL=.*|CONFLUENT_SCHEMA_REGISTRY_URL=http://localhost:8081|' .env

# Comment out Confluent Cloud credentials
sed -i '' 's|^CONFLUENT_API_KEY=|# CONFLUENT_API_KEY=|' .env
sed -i '' 's|^CONFLUENT_API_SECRET=|# CONFLUENT_API_SECRET=|' .env

echo "✅ .env 已更新为本地 Kafka"

# Start Docker services
echo ""
echo "启动本地 Kafka 服务..."
cd deployment
docker-compose up -d zookeeper kafka schema-registry postgres redis

echo ""
echo "等待服务启动..."
sleep 15

# Check services
echo ""
echo "检查服务状态:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(kafka|zookeeper|schema-registry|postgres|redis)"

# Create topics
echo ""
echo "创建 Kafka Topics..."
cd ..
python3 scripts/create_topics.py

echo ""
echo "=========================================="
echo "✅ 切换完成！"
echo "=========================================="
echo ""
echo "💰 费用节省:"
echo "  - Confluent Cloud: 已停止使用"
echo "  - 本地 Kafka: 免费 (Docker)"
echo ""
echo "📋 验证连接:"
echo "  docker exec -it deployment-kafka-1 kafka-topics --list --bootstrap-server localhost:9092"
echo ""
echo "🔄 如需切换回 Confluent Cloud:"
echo "  1. 恢复 .env.backup 文件"
echo "  2. 或手动修改 .env 中的配置"

