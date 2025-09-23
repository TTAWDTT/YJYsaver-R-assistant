"""
提示词系统测试脚本
测试新的模块化提示词系统
"""

import os
import sys
import django

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r_assistant'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'r_assistant.settings')
django.setup()

from services.advanced_prompt_manager import advanced_prompt_manager
from services.prompt_manager import PromptManager


def test_prompt_system():
    """测试提示词系统"""
    print("=" * 60)
    print("提示词系统测试")
    print("=" * 60)
    
    # 1. 测试可用提示词列表
    print("\n1. 可用提示词类型:")
    available = advanced_prompt_manager.list_available_prompts()
    for category, prompts in available.items():
        print(f"   {category}: {len(prompts)} 个提示词")
        for prompt in prompts[:3]:  # 只显示前3个
            print(f"     - {prompt}")
        if len(prompts) > 3:
            print(f"     ... 还有 {len(prompts)-3} 个")
    
    # 2. 测试提示词验证
    print("\n2. 提示词验证结果:")
    validation = advanced_prompt_manager.validate_prompts()
    print(f"   ✅ 有效提示词: {len(validation['valid'])} 个")
    print(f"   ❌ 无效提示词: {len(validation['invalid'])} 个")
    print(f"   ⚠️  警告: {len(validation['warnings'])} 个")
    
    if validation['invalid']:
        print("   无效提示词详情:")
        for invalid in validation['invalid'][:3]:
            print(f"     - {invalid}")
    
    # 3. 测试具体提示词获取
    print("\n3. 测试具体提示词:")
    
    # 代码解释提示
    try:
        explain_prompt = advanced_prompt_manager.get_prompt(
            'code_explainer', 'user_template',
            code="x <- 1:10\nprint(x)",
            additional_context="这是一个简单示例"
        )
        print("   ✅ 代码解释提示词生成成功")
        print(f"   长度: {len(explain_prompt)} 字符")
    except Exception as e:
        print(f"   ❌ 代码解释提示词生成失败: {e}")
    
    # 问题解决提示
    try:
        solver_prompt = advanced_prompt_manager.get_prompt(
            'problem_solver', 'user_template',
            problem_description="如何在R中创建散点图",
            additional_requirements="使用ggplot2包"
        )
        print("   ✅ 问题解决提示词生成成功")
        print(f"   长度: {len(solver_prompt)} 字符")
    except Exception as e:
        print(f"   ❌ 问题解决提示词生成失败: {e}")
    
    # 对话提示
    try:
        chat_prompt = advanced_prompt_manager.get_prompt(
            'conversation', 'user_template',
            message="你好，我想学习R语言",
            conversation_context=""
        )
        print("   ✅ 对话提示词生成成功")
        print(f"   长度: {len(chat_prompt)} 字符")
    except Exception as e:
        print(f"   ❌ 对话提示词生成失败: {e}")
    
    # 4. 测试兼容性接口
    print("\n4. 测试兼容性接口:")
    
    try:
        old_explain = PromptManager.get_explain_prompt("data <- c(1,2,3)")
        print("   ✅ 兼容性代码解释接口正常")
        print(f"   长度: {len(old_explain)} 字符")
    except Exception as e:
        print(f"   ❌ 兼容性代码解释接口失败: {e}")
    
    try:
        old_answer = PromptManager.get_answer_prompt("如何计算平均值")
        print("   ✅ 兼容性问题解决接口正常")
        print(f"   长度: {len(old_answer)} 字符")
    except Exception as e:
        print(f"   ❌ 兼容性问题解决接口失败: {e}")
    
    # 5. 测试新增功能
    print("\n5. 测试新增功能:")
    
    try:
        data_analysis_prompt = PromptManager.get_data_analysis_prompt(
            "包含销售数据的CSV文件",
            "分析销售趋势",
            "生成趋势图表"
        )
        print("   ✅ 数据分析提示词生成成功")
        print(f"   长度: {len(data_analysis_prompt)} 字符")
    except Exception as e:
        print(f"   ❌ 数据分析提示词生成失败: {e}")
    
    try:
        viz_prompt = PromptManager.get_visualization_prompt(
            "数值型变量x和y",
            "散点图",
            "展示相关性"
        )
        print("   ✅ 可视化提示词生成成功")
        print(f"   长度: {len(viz_prompt)} 字符")
    except Exception as e:
        print(f"   ❌ 可视化提示词生成失败: {e}")
    
    # 6. 测试提示词信息
    print("\n6. 提示词详细信息示例:")
    
    try:
        info = advanced_prompt_manager.get_prompt_info('code_explainer', 'system')
        print(f"   类别: {info['category']}")
        print(f"   类型: {info['type']}")
        print(f"   长度: {info['length']} 字符")
        print(f"   模板变量: {info['template_variables']}")
        print(f"   预览: {info['preview'][:100]}...")
    except Exception as e:
        print(f"   ❌ 获取提示词信息失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 提示词系统测试完成！")
    print("📁 提示词文件位置: r_assistant/prompts/")
    print("🔧 管理器位置: r_assistant/services/advanced_prompt_manager.py")
    print("🔄 兼容接口: r_assistant/services/prompt_manager.py")
    print("=" * 60)


if __name__ == "__main__":
    test_prompt_system()