# 使用 Dockerfile 部署（如果 Render 支持 Docker）
FROM python:3.11-slim

# 安装系统依赖（librdkafka 需要）
RUN apt-get update && apt-get install -y \
    librdkafka-dev \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY dispatch_center.py .

# 暴露端口（Render 会设置 PORT 环境变量）
EXPOSE 10000

# 启动应用
CMD ["python", "dispatch_center.py"]
