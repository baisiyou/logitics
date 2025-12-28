# Render Python 版本配置说明

## ⚠️ 重要：Python 版本兼容性

如果遇到 `ModuleNotFoundError: No module named 'kafka.vendor.six.moves'` 错误，这是因为 `kafka-python` 与 Python 3.13 存在兼容性问题。

## 解决方案：指定 Python 3.11

### 方法 1：使用 runtime.txt（推荐）

确保 `applications/scheduler/runtime.txt` 文件存在并包含：
```
python-3.11.0
```

### 方法 2：在 Render Dashboard 中设置

1. 进入服务设置
2. 找到 **Environment Variables** 部分
3. 添加环境变量：
   - **Key**: `PYTHON_VERSION`
   - **Value**: `3.11.0`

### 方法 3：使用 Dockerfile

如果使用 Dockerfile 部署，确保 Dockerfile 使用 Python 3.11：
```dockerfile
FROM python:3.11-slim
```

## 为什么使用 Python 3.11？

- Python 3.11 是最稳定的版本之一
- 所有依赖包（kafka-python, pydantic, fastapi）都完全支持
- Render 默认支持 Python 3.11
- 避免 Python 3.13 的新特性导致的兼容性问题

## 验证

部署后，在服务日志中应该看到：
```
Python 3.11.x
```

而不是：
```
Python 3.13.x
```

