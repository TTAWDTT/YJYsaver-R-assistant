#!/usr/bin/env python
"""
测试修复后的系统功能
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'r_assistant'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'r_assistant.settings')
django.setup()

from services.langgraph_service import langgraph_service

def test_system_functions():
    """测试系统各项功能"""
    print("=" * 60)
    print("系统功能测试")
    print("=" * 60)
    
    # 测试1：聊天功能
    print("\n1. 测试聊天功能...")
    try:
        result = langgraph_service.chat("你好，我是新手，如何学习R语言？")
        if result['success']:
            print("✅ 聊天功能正常")
            print(f"   响应内容: {result['content'][:100]}...")
            print(f"   处理时间: {result.get('processing_time', 0):.2f}秒")
        else:
            print("❌ 聊天功能失败")
    except Exception as e:
        print(f"❌ 聊天功能异常: {str(e)}")
    
    # 测试2：代码解释功能  
    print("\n2. 测试代码解释功能...")
    try:
        test_code = """
        library(ggplot2)
        data(mtcars)
        ggplot(mtcars, aes(x=mpg, y=hp)) + 
          geom_point() +
          geom_smooth(method="lm")
        """
        result = langgraph_service.explain_code(test_code)
        if result['success']:
            print("✅ 代码解释功能正常")
            print(f"   解释内容: {result['content'][:100]}...")
            print(f"   处理时间: {result.get('processing_time', 0):.2f}秒")
        else:
            print("❌ 代码解释功能失败")
    except Exception as e:
        print(f"❌ 代码解释功能异常: {str(e)}")
    
    # 测试3：问题求解功能
    print("\n3. 测试问题求解功能...")
    try:
        result = langgraph_service.solve_problem("如何在R中创建一个散点图？")
        if result['success']:
            print("✅ 问题求解功能正常")
            print(f"   解答内容: {result['content'][:100]}...")
            print(f"   处理时间: {result.get('processing_time', 0):.2f}秒")
        else:
            print("❌ 问题求解功能失败")
    except Exception as e:
        print(f"❌ 问题求解功能异常: {str(e)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("如果所有功能都显示 ✅，则表示系统已完全修复。")
    print("如果有 ❌，请检查相关配置或查看错误信息。")
    print("=" * 60)

if __name__ == "__main__":
    test_system_functions()