#!/bin/bash
# Render 构建脚本
# 安装 Python 依赖

set -e  # 遇到错误立即退出

echo "升级 pip..."
pip install --upgrade pip

echo "安装 Python 依赖..."
pip install -r requirements.txt

echo "构建完成！"
