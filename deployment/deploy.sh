#!/bin/bash

# 亚马逊物流网络实时智能调度系统部署脚本

set -e

echo "=========================================="
echo "开始部署亚马逊物流智能调度系统"
echo "=========================================="

# 检查环境变量
if [ ! -f .env ]; then
    echo "错误: .env 文件不存在"
    echo "请复制 .env.example 到 .env 并填写配置"
    exit 1
fi

# 加载环境变量
export $(cat .env | grep -v '^#' | xargs)

# 1. 启动基础设施
echo "1. 启动Docker基础设施..."
cd deployment
docker-compose up -d zookeeper kafka schema-registry ksqldb-server postgres redis

echo "等待服务启动..."
sleep 30

# 2. 创建Kafka Topics
echo "2. 创建Kafka Topics..."
cd ..
# 等待 Kafka 完全就绪
echo "等待 Kafka 就绪..."
for i in {1..30}; do
    if docker exec deployment-kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null; then
        break
    fi
    sleep 1
done
python3 scripts/create_topics.py
cd deployment

# 3. 初始化ksqlDB查询
echo "3. 初始化ksqlDB查询..."
sleep 15

# 确保 ksqlDB server 运行
if ! docker ps | grep -q ksqldb-server; then
    echo "启动 ksqlDB server..."
    docker-compose up -d ksqldb-server
    sleep 10
fi

# 等待 ksqlDB 就绪
echo "等待 ksqlDB 就绪..."
for i in {1..30}; do
    if curl -s http://localhost:8088/info > /dev/null 2>&1; then
        echo "ksqlDB 已就绪"
        break
    fi
    sleep 2
done

# 启动 CLI 容器并执行查询
if [ -f ../confluent/ksqldb/queries.sql ]; then
    echo "执行 ksqlDB 查询..."
    docker-compose up -d ksqldb-cli
    sleep 5
    
    if docker ps | grep -q ksqldb-cli; then
        docker exec -i deployment-ksqldb-cli-1 ksql http://ksqldb-server:8088 < ../confluent/ksqldb/queries.sql 2>&1 | grep -v "^ksql>" || echo "ksqlDB 查询执行完成"
    else
        echo "ksqlDB CLI 未运行，跳过查询初始化（可在 ksqlDB UI 中手动执行）"
    fi
else
    echo "未找到 ksqlDB 查询文件，跳过"
fi

# 4. 启动数据源模拟器
echo "4. 启动数据源模拟器..."
cd ../data-sources/simulators
python3 order_simulator.py &
ORDER_PID=$!
python3 vehicle_location_simulator.py &
VEHICLE_PID=$!
python3 inventory_simulator.py &
INVENTORY_PID=$!

echo "数据源模拟器已启动 (PIDs: $ORDER_PID, $VEHICLE_PID, $INVENTORY_PID)"

# 5. 启动流处理器
echo "5. 启动流处理器..."
cd ../../confluent/stream_processors
python3 order_enricher.py &
ENRICHER_PID=$!
python3 stream_joiner.py &
JOINER_PID=$!

echo "流处理器已启动 (PIDs: $ENRICHER_PID, $JOINER_PID)"

# 6. 启动AI服务
echo "6. 启动AI推理服务..."
cd ../../ai-inference
python3 vertex_ai_service.py &
AI_SERVICE_PID=$!
sleep 5
python3 kafka_ai_processor.py &
AI_PROCESSOR_PID=$!

echo "AI服务已启动 (PIDs: $AI_SERVICE_PID, $AI_PROCESSOR_PID)"

# 7. 启动应用层服务
echo "7. 启动应用层服务..."
cd ../../applications

# 调度中心
cd scheduler
python3 dispatch_center.py &
DISPATCH_PID=$!

# 司机APP
cd ../driver_app
python3 driver_api.py &
DRIVER_PID=$!

# 仓库预警
cd ../warehouse
python3 warehouse_alert_system.py &
WAREHOUSE_PID=$!

# 客户ETA服务
cd ../customer
python3 customer_eta_service.py &
CUSTOMER_PID=$!

echo "应用层服务已启动"
echo "  调度中心: http://localhost:8001"
echo "  司机APP: http://localhost:8002"
echo "  仓库预警: http://localhost:8003"
echo "  客户ETA: http://localhost:8004"

# 8. 保存PID到文件
cd ../..
echo "$ORDER_PID $VEHICLE_PID $INVENTORY_PID $ENRICHER_PID $JOINER_PID $AI_SERVICE_PID $AI_PROCESSOR_PID $DISPATCH_PID $DRIVER_PID $WAREHOUSE_PID $CUSTOMER_PID" > .pids

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "服务状态:"
echo "  - Kafka: localhost:9092"
echo "  - Schema Registry: http://localhost:8081"
echo "  - ksqlDB: http://localhost:8088"
echo "  - 调度中心: http://localhost:8001"
echo "  - 司机APP: http://localhost:8002"
echo "  - 仓库预警: http://localhost:8003"
echo "  - 客户ETA: http://localhost:8004"
echo ""
echo "停止所有服务: ./stop.sh"
echo "查看日志: docker-compose -f deployment/docker-compose.yml logs -f"

