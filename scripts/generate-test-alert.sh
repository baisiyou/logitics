#!/bin/bash

# Generate test alerts for testing

set -e

echo "=========================================="
echo "生成测试警报"
echo "=========================================="

# Test anomaly alert
echo "1. 生成异常警报..."
curl -s -X POST http://localhost:8000/api/v1/detect/anomaly \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "order",
    "features": {
      "item_count": 25,
      "total_weight": 60,
      "priority": "STANDARD"
    }
  }' | python3 -m json.tool

echo ""
echo "2. 生成仓库压力警报..."
curl -s -X POST http://localhost:8000/api/v1/predict/warehouse-pressure \
  -H "Content-Type: application/json" \
  -d '{
    "warehouse_id": "WH001",
    "current_orders": 950,
    "current_capacity": 1000,
    "pending_orders": 100,
    "historical_data": []
  }' | python3 -m json.tool

echo ""
echo "3. 检查警报是否到达调度中心..."
sleep 3
curl -s http://localhost:8001/api/v1/alerts?limit=5 | python3 -m json.tool

echo ""
echo "✅ 测试完成"

