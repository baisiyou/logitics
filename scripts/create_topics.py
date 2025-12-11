#!/usr/bin/env python3
"""
创建Kafka Topics脚本
"""

import json
from confluent_kafka.admin import AdminClient, NewTopic
import os
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092')


def create_topics():
    """创建所有Kafka Topics"""
    admin = AdminClient({'bootstrap.servers': BOOTSTRAP_SERVERS})
    
    # 读取topics配置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    topics_file = os.path.join(script_dir, '..', 'data-sources', 'kafka_topics.json')
    
    with open(topics_file) as f:
        topics_config = json.load(f)
    
    # 创建topics
    topics = []
    for topic_config in topics_config['topics']:
        topic = NewTopic(
            topic_config['name'],
            num_partitions=topic_config['partitions'],
            replication_factor=topic_config['replication_factor'],
            config=topic_config.get('config', {})
        )
        topics.append(topic)
    
    # 执行创建
    fs = admin.create_topics(topics)
    
    results = []
    for topic, f in fs.items():
        try:
            f.result()  # 等待结果
            print(f'✓ Topic {topic} 创建成功')
            results.append((topic, True, None))
        except Exception as e:
            error_str = str(e)
            # 如果 topic 已存在，视为成功
            if 'TOPIC_ALREADY_EXISTS' in error_str or 'already exists' in error_str.lower():
                print(f'✓ Topic {topic} 已存在（跳过）')
                results.append((topic, True, None))
            else:
                print(f'✗ Topic {topic} 创建失败: {e}')
                results.append((topic, False, str(e)))
    
    return results


if __name__ == '__main__':
    print("开始创建Kafka Topics...")
    print(f"Bootstrap Servers: {BOOTSTRAP_SERVERS}")
    print("-" * 50)
    
    results = create_topics()
    
    print("-" * 50)
    success_count = sum(1 for _, success, _ in results if success)
    print(f"完成: {success_count}/{len(results)} topics 创建成功")

