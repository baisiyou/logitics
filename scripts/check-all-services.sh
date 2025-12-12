#!/bin/bash

# Check all services status

set -e

echo "=========================================="
echo "检查所有服务状态"
echo "=========================================="
echo ""

# Docker services
echo "1. Docker 服务:"
echo "----------------------------------------"
cd "$(dirname "$0")/../deployment"
docker-compose ps 2>/dev/null || echo "Docker Compose 未运行"

echo ""
echo "2. Kafka Topics:"
echo "----------------------------------------"
TOPICS=$(docker exec deployment-kafka-1 kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null | wc -l | tr -d ' ')
if [ "$TOPICS" -gt 0 ]; then
    echo "   ✅ Topics 数量: $TOPICS"
    echo "   前 10 个 topics:"
    docker exec deployment-kafka-1 kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null | head -10
else
    echo "   ⚠️  无 topics 或 Kafka 未运行"
fi

echo ""
echo "3. 服务健康检查:"
echo "----------------------------------------"

# Kafka
if docker exec deployment-kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null; then
    echo "   ✅ Kafka: 正常"
else
    echo "   ❌ Kafka: 异常"
fi

# Schema Registry
if curl -s http://localhost:8081/subjects &>/dev/null; then
    echo "   ✅ Schema Registry: 正常"
else
    echo "   ❌ Schema Registry: 异常"
fi

# ksqlDB
if curl -s http://localhost:8088/info &>/dev/null; then
    echo "   ✅ ksqlDB: 正常"
else
    echo "   ⚠️  ksqlDB: 未运行或启动中"
fi

# PostgreSQL
if docker exec deployment-postgres-1 pg_isready -U logistics_user &>/dev/null; then
    echo "   ✅ PostgreSQL: 正常"
else
    echo "   ❌ PostgreSQL: 异常"
fi

# Redis
if docker exec deployment-redis-1 redis-cli ping &>/dev/null | grep -q PONG; then
    echo "   ✅ Redis: 正常"
else
    echo "   ❌ Redis: 异常"
fi

echo ""
echo "4. Python 服务:"
echo "----------------------------------------"
PYTHON_SERVICES=$(ps aux | grep -E "(vertex_ai|dispatch|driver|warehouse|customer|simulator)" | grep python3 | grep -v grep | wc -l | tr -d ' ')
echo "   运行中的服务: $PYTHON_SERVICES"
if [ "$PYTHON_SERVICES" -gt 0 ]; then
    ps aux | grep -E "(vertex_ai|dispatch|driver|warehouse|customer|simulator)" | grep python3 | grep -v grep | awk '{print "      - " $11 " " $12}'
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

