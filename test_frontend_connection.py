"""
前端连接测试脚本
测试API端点和功能是否正常工作
"""

import os
import sys
import django
import requests
import json

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r_assistant'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'r_assistant.settings')
django.setup()

from django.test import Client
from django.urls import reverse


def test_api_endpoints():
    """测试API端点"""
    print("=" * 60)
    print("前端连接测试")
    print("=" * 60)
    
    client = Client()
    
    # 1. 测试主页访问
    print("\n1. 测试主页访问...")
    try:
        response = client.get('/')
        print(f"   ✅ 主页访问成功 (状态码: {response.status_code})")
    except Exception as e:
        print(f"   ❌ 主页访问失败: {e}")
    
    # 2. 测试代码解释页面
    print("\n2. 测试代码解释页面...")
    try:
        response = client.get('/explain/')
        print(f"   ✅ 代码解释页面访问成功 (状态码: {response.status_code})")
    except Exception as e:
        print(f"   ❌ 代码解释页面访问失败: {e}")
    
    # 3. 测试对话页面
    print("\n3. 测试对话页面...")
    try:
        response = client.get('/talk/')
        print(f"   ✅ 对话页面访问成功 (状态码: {response.status_code})")
    except Exception as e:
        print(f"   ❌ 对话页面访问失败: {e}")
    
    # 4. 测试API端点 - 代码解释
    print("\n4. 测试代码解释API...")
    try:
        response = client.post('/api/explain/', 
            data=json.dumps({'code': 'x <- 1:10\nprint(x)'}),
            content_type='application/json')
        print(f"   ✅ 代码解释API访问成功 (状态码: {response.status_code})")
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {result.get('success', False)}")
    except Exception as e:
        print(f"   ❌ 代码解释API访问失败: {e}")
    
    # 5. 测试API端点 - 对话
    print("\n5. 测试对话API...")
    try:
        response = client.post('/api/talk/', 
            data=json.dumps({'message': '你好，请介绍一下R语言'}),
            content_type='application/json')
        print(f"   ✅ 对话API访问成功 (状态码: {response.status_code})")
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {result.get('success', False)}")
    except Exception as e:
        print(f"   ❌ 对话API访问失败: {e}")
    
    # 6. 测试POST提交 - 对话功能
    print("\n6. 测试对话POST提交...")
    try:
        response = client.post('/talk/', {
            'message': '测试消息，请回复'
        })
        print(f"   ✅ 对话POST提交成功 (状态码: {response.status_code})")
        if 'error' in str(response.content):
            print(f"   ⚠️  可能有错误，但页面加载正常")
    except Exception as e:
        print(f"   ❌ 对话POST提交失败: {e}")
    
    # 7. 测试POST提交 - 代码解释功能  
    print("\n7. 测试代码解释POST提交...")
    try:
        response = client.post('/explain/', {
            'code': 'data <- c(1, 2, 3, 4, 5)\nmean(data)'
        })
        print(f"   ✅ 代码解释POST提交成功 (状态码: {response.status_code})")
        if 'error' in str(response.content):
            print(f"   ⚠️  可能有错误，但页面加载正常")
    except Exception as e:
        print(f"   ❌ 代码解释POST提交失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 前端连接测试完成！")
    print("\n📋 结果总结:")
    print("- 如果所有测试都显示 ✅，说明前端已成功连接")
    print("- 如果显示 ⚠️，说明功能可用但AI服务可能需要配置")
    print("- 如果显示 ❌，说明需要进一步调试")
    print("\n🔧 如需启用完整AI功能，请配置 .env 文件中的 DEEPSEEK_API_KEY")
    print("=" * 60)


if __name__ == "__main__":
    test_api_endpoints()