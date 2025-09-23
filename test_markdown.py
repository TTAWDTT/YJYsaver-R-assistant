#!/usr/bin/env python
"""
测试Markdown渲染效果
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'r_assistant'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'r_assistant.settings')
django.setup()

from core.templatetags.markdown_filters import markdown_filter

def test_markdown_rendering():
    """测试Markdown渲染效果"""
    print("=" * 60)
    print("Markdown渲染测试")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "标题测试",
            "content": "# 主标题\n## 二级标题\n### 三级标题"
        },
        {
            "name": "文本格式",
            "content": "这是**粗体**和*斜体*文本。"
        },
        {
            "name": "列表测试",
            "content": "- 项目1\n- 项目2\n- 项目3"
        },
        {
            "name": "内联代码",
            "content": "使用 `print()` 函数输出内容。"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        print(f"输入: {repr(test_case['content'])}")
        result = markdown_filter(test_case['content'])
        print(f"输出: {result}")
        print("-" * 40)

if __name__ == "__main__":
    test_markdown_rendering()