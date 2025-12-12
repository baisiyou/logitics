#!/bin/bash

# 停止所有服务

echo "停止所有服务..."

# 停止Python进程
if [ -f .pids ]; then
    PIDS=$(cat .pids)
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo "已停止进程 $PID"
        fi
    done
    rm .pids
fi

# 停止Docker服务
cd deployment
docker-compose down

echo "所有服务已停止"

