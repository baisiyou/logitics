# debug_credentials.py
import os
import sys
import json
from pathlib import Path

print("🔍 开始调试 Google Cloud 凭证...")
print("=" * 50)

# 1. 检查当前目录
print(f"当前工作目录: {os.getcwd()}")

# 2. 检查文件路径
creds_path = Path("config/gcp-credentials.json")
print(f"查找文件: {creds_path.absolute()}")

if creds_path.exists():
    print(f"✅ 文件存在!")
    print(f"   文件大小: {creds_path.stat().st_size} 字节")
    
    # 检查文件内容
    try:
        with open(creds_path, 'r') as f:
            content = f.read()
            
        # 尝试解析JSON
        data = json.loads(content)
        print(f"✅ JSON 解析成功!")
        print(f"   项目ID: {data.get('project_id', '未找到')}")
        print(f"   账号邮箱: {data.get('client_email', '未找到')}")
        print(f"   密钥类型: {data.get('type', '未找到')}")
        
        # 检查必要字段
        required = ['type', 'project_id', 'private_key', 'client_email', 'private_key_id']
        missing = [field for field in required if field not in data]
        
        if missing:
            print(f"⚠️  缺少字段: {missing}")
        else:
            print(f"✅ 所有必要字段完整")
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print("前100个字符:", content[:100] if content else "空文件")
    except Exception as e:
        print(f"❌ 读取文件时出错: {type(e).__name__}: {e}")
        
else:
    print(f"❌ 文件不存在!")
    
    # 检查config目录是否存在
    config_dir = Path("config")
    if config_dir.exists():
        print(f"✅ config 目录存在")
        print(f"   目录内容: {list(config_dir.iterdir())}")
    else:
        print(f"❌ config 目录不存在")

print("=" * 50)

# 3. 测试导入google库
print("测试导入Google库...")
try:
    from google.oauth2 import service_account
    print("✅ 可以导入 google.oauth2")
    
    if creds_path.exists():
        try:
            creds = service_account.Credentials.from_service_account_file(
                str(creds_path),
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            print("✅ 凭证文件有效!")
            print(f"   服务账号: {creds.service_account_email}")
        except Exception as e:
            print(f"❌ 加载凭证失败: {type(e).__name__}: {e}")
            
except ImportError as e:
    print(f"❌ 无法导入Google库: {e}")
    print("请安装: pip install google-auth google-auth-oauthlib")

print("=" * 50)
print("调试完成")