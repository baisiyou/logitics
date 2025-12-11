#!/bin/bash

# Stop all Amazon Logistics services

set -e

echo "=========================================="
echo "Stopping Amazon Logistics Services"
echo "=========================================="

# Find and stop Python services
echo "Stopping Python services..."

# Vertex AI Service
VERTEX_PID=$(ps aux | grep "vertex_ai_service.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$VERTEX_PID" ]; then
    echo "Stopping Vertex AI Service (PID: $VERTEX_PID)..."
    kill $VERTEX_PID 2>/dev/null || true
    sleep 1
    # Force kill if still running
    kill -9 $VERTEX_PID 2>/dev/null || true
    echo "✅ Vertex AI Service stopped"
fi

# Kafka AI Processor
KAFKA_AI_PID=$(ps aux | grep "kafka_ai_processor.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$KAFKA_AI_PID" ]; then
    echo "Stopping Kafka AI Processor (PID: $KAFKA_AI_PID)..."
    kill $KAFKA_AI_PID 2>/dev/null || true
    sleep 1
    kill -9 $KAFKA_AI_PID 2>/dev/null || true
    echo "✅ Kafka AI Processor stopped"
fi

# Dispatch Center
DISPATCH_PID=$(ps aux | grep "dispatch_center.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$DISPATCH_PID" ]; then
    echo "Stopping Dispatch Center (PID: $DISPATCH_PID)..."
    kill $DISPATCH_PID 2>/dev/null || true
    sleep 1
    kill -9 $DISPATCH_PID 2>/dev/null || true
    echo "✅ Dispatch Center stopped"
fi

# Driver API
DRIVER_PID=$(ps aux | grep "driver_api.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$DRIVER_PID" ]; then
    echo "Stopping Driver API (PID: $DRIVER_PID)..."
    kill $DRIVER_PID 2>/dev/null || true
    sleep 1
    kill -9 $DRIVER_PID 2>/dev/null || true
    echo "✅ Driver API stopped"
fi

# Warehouse Alert
WAREHOUSE_PID=$(ps aux | grep "warehouse_alert_system.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$WAREHOUSE_PID" ]; then
    echo "Stopping Warehouse Alert System (PID: $WAREHOUSE_PID)..."
    kill $WAREHOUSE_PID 2>/dev/null || true
    sleep 1
    kill -9 $WAREHOUSE_PID 2>/dev/null || true
    echo "✅ Warehouse Alert System stopped"
fi

# Customer ETA
CUSTOMER_PID=$(ps aux | grep "customer_eta_service.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$CUSTOMER_PID" ]; then
    echo "Stopping Customer ETA Service (PID: $CUSTOMER_PID)..."
    kill $CUSTOMER_PID 2>/dev/null || true
    sleep 1
    kill -9 $CUSTOMER_PID 2>/dev/null || true
    echo "✅ Customer ETA Service stopped"
fi

# Stream Processors
ENRICHER_PID=$(ps aux | grep "order_enricher.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$ENRICHER_PID" ]; then
    echo "Stopping Order Enricher (PID: $ENRICHER_PID)..."
    kill $ENRICHER_PID 2>/dev/null || true
    sleep 1
    kill -9 $ENRICHER_PID 2>/dev/null || true
    echo "✅ Order Enricher stopped"
fi

JOINER_PID=$(ps aux | grep "stream_joiner.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$JOINER_PID" ]; then
    echo "Stopping Stream Joiner (PID: $JOINER_PID)..."
    kill $JOINER_PID 2>/dev/null || true
    sleep 1
    kill -9 $JOINER_PID 2>/dev/null || true
    echo "✅ Stream Joiner stopped"
fi

# Simulators
ORDER_SIM_PID=$(ps aux | grep "order_simulator.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$ORDER_SIM_PID" ]; then
    echo "Stopping Order Simulator (PID: $ORDER_SIM_PID)..."
    kill $ORDER_SIM_PID 2>/dev/null || true
    sleep 1
    kill -9 $ORDER_SIM_PID 2>/dev/null || true
    echo "✅ Order Simulator stopped"
fi

VEHICLE_SIM_PID=$(ps aux | grep "vehicle_location_simulator.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$VEHICLE_SIM_PID" ]; then
    echo "Stopping Vehicle Simulator (PID: $VEHICLE_SIM_PID)..."
    kill $VEHICLE_SIM_PID 2>/dev/null || true
    sleep 1
    kill -9 $VEHICLE_SIM_PID 2>/dev/null || true
    echo "✅ Vehicle Simulator stopped"
fi

INVENTORY_SIM_PID=$(ps aux | grep "inventory_simulator.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$INVENTORY_SIM_PID" ]; then
    echo "Stopping Inventory Simulator (PID: $INVENTORY_SIM_PID)..."
    kill $INVENTORY_SIM_PID 2>/dev/null || true
    sleep 1
    kill -9 $INVENTORY_SIM_PID 2>/dev/null || true
    echo "✅ Inventory Simulator stopped"
fi

# Check for any remaining processes
REMAINING=$(ps aux | grep -E "(vertex_ai|kafka_ai|dispatch|driver|warehouse|customer|simulator|enricher|joiner)" | grep python3 | grep -v grep | wc -l | tr -d ' ')

if [ "$REMAINING" -gt 0 ]; then
    echo ""
    echo "⚠️  Some processes may still be running:"
    ps aux | grep -E "(vertex_ai|kafka_ai|dispatch|driver|warehouse|customer|simulator|enricher|joiner)" | grep python3 | grep -v grep
else
    echo ""
    echo "✅ All services stopped"
fi

echo ""
echo "=========================================="
echo "Stopped all services"
echo "=========================================="

