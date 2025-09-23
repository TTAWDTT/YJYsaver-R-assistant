#!/usr/bin/env python
"""
测试Django应用的修复
"""
import os
import sys
import django

# 设置Django环境
sys.path.append('r_assistant')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'r_assistant.settings')
django.setup()

from core.models import RequestLog, CodeSolution, ConversationHistory, UserSession

def test_models():
    """测试模型定义"""
    print("测试模型...")
    
    # 测试字段存在
    request_log_fields = [field.name for field in RequestLog._meta.fields]
    print(f"RequestLog字段: {request_log_fields}")
    
    code_solution_fields = [field.name for field in CodeSolution._meta.fields]
    print(f"CodeSolution字段: {code_solution_fields}")
    
    # 检查关键字段
    assert 'session_id' in request_log_fields, "RequestLog缺少session_id字段"
    assert 'request_log' in code_solution_fields, "CodeSolution缺少request_log字段"
    assert 'input_content' in request_log_fields, "RequestLog缺少input_content字段"
    assert 'response_content' in request_log_fields, "RequestLog缺少response_content字段"
    
    print("✓ 模型字段检查通过")

def test_views_import():
    """测试视图导入"""
    print("测试视图导入...")
    
    try:
        from core.views import IndexView, ExplainView, AnswerView, TalkView, HistoryView
        print("✓ 视图类导入成功")
    except ImportError as e:
        print(f"✗ 视图导入失败: {e}")
        return False
    
    return True

def test_ai_response():
    """测试AI回复函数"""
    print("测试AI回复函数...")
    
    from core.views import simple_ai_response
    
    # 测试explain类型
    result = simple_ai_response('explain', 'print("hello")')
    assert isinstance(result, str), "explain应该返回字符串"
    
    # 测试answer类型
    result = simple_ai_response('answer', '如何计算平均数')
    assert isinstance(result, tuple), "answer应该返回元组"
    assert len(result) == 2, "answer应该返回(response, solutions)"
    
    # 测试talk类型
    result = simple_ai_response('talk', '你好')
    assert isinstance(result, str), "talk应该返回字符串"
    
    print("✓ AI回复函数测试通过")

def main():
    """主测试函数"""
    print("开始测试Django应用修复...")
    print("=" * 50)
    
    try:
        test_models()
        test_views_import()
        test_ai_response()
        
        print("=" * 50)
        print("✓ 所有测试通过！应用已修复成功")
        return True
        
    except Exception as e:
        print("=" * 50)
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)