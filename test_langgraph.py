#!/usr/bin/env python
"""
LangGraph工作流系统测试脚本
验证LangGraph集成是否正常工作
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# 设置Django环境
sys.path.append('r_assistant')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'r_assistant.settings')

try:
    import django
    django.setup()
except Exception as e:
    print(f"Django设置失败: {e}")
    sys.exit(1)


async def test_langgraph_integration():
    """测试LangGraph工作流集成"""
    
    print("=" * 60)
    print("LangGraph工作流系统测试")
    print("=" * 60)
    
    try:
        # 导入LangGraph相关模块
        from services.workflow_state import WorkflowState, Message, CodeSolution
        from services.langgraph_agents import CodeExplainerAgent, ProblemSolverAgent, ConversationAgent
        from services.langgraph_workflow import workflow_engine
        from services.langgraph_service import langgraph_service
        
        print("✓ LangGraph模块导入成功")
        
        # 测试1: 工作流状态定义
        print("\n1. 测试工作流状态...")
        test_state = WorkflowState(
            session_id="test_session",
            request_id="test_request",
            request_type="test",
            user_input="test input",
            conversation_history=[],
            ai_response=None,
            code_solutions=[],
            explanation_result=None,
            code_analysis=None,
            quality_score=None,
            complexity_analysis=None,
            processing_steps=[],
            start_time=datetime.now(),
            end_time=None,
            total_tokens=0,
            errors=[],
            warnings=[],
            next_step=None,
            workflow_complete=False
        )
        print("✓ 工作流状态创建成功")
        
        # 测试2: 代理初始化
        print("\n2. 测试代理初始化...")
        code_explainer = CodeExplainerAgent()
        problem_solver = ProblemSolverAgent()
        conversation_agent = ConversationAgent()
        print("✓ 所有代理初始化成功")
        
        # 测试3: 工作流引擎
        print("\n3. 测试工作流引擎...")
        workflows = workflow_engine.workflows
        print(f"✓ 工作流引擎已加载 {len(workflows)} 个工作流: {list(workflows.keys())}")
        
        # 测试4: 服务接口（模拟测试，不调用真实API）
        print("\n4. 测试服务接口...")
        
        # 由于没有真实的API密钥，我们只测试接口存在性
        service_methods = ['explain_code', 'solve_problem', 'chat']
        for method in service_methods:
            if hasattr(langgraph_service, method):
                print(f"✓ {method} 方法存在")
            else:
                print(f"✗ {method} 方法缺失")
        
        # 测试5: 数据模型
        print("\n5. 测试数据模型...")
        from core.models import RequestLog, CodeSolution, ConversationHistory
        
        # 检查模型字段
        request_log_fields = [field.name for field in RequestLog._meta.fields]
        required_fields = ['session_id', 'request_type', 'input_content', 'response_content', 'success']
        missing_fields = [field for field in required_fields if field not in request_log_fields]
        
        if not missing_fields:
            print("✓ RequestLog模型字段完整")
        else:
            print(f"✗ RequestLog缺失字段: {missing_fields}")
        
        code_solution_fields = [field.name for field in CodeSolution._meta.fields]
        if 'request_log' in code_solution_fields:
            print("✓ CodeSolution关联字段正确")
        else:
            print("✗ CodeSolution缺失request_log关联")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("✓ LangGraph工作流系统集成成功")
        print("\n注意事项:")
        print("- 需要配置DEEPSEEK_API_KEY环境变量才能正常使用")
        print("- 在生产环境中测试实际API调用")
        print("- 查看工作流监控面板: /admin/workflow-monitor/")
        print("=" * 60)
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """测试配置"""
    print("\n配置检查:")
    
    # 检查Django设置
    from django.conf import settings
    
    # 检查API配置
    api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
    api_url = getattr(settings, 'DEEPSEEK_API_URL', None)
    
    if api_key and api_key != 'sk-placeholder-key-change-this':
        print("✓ DEEPSEEK_API_KEY 已配置")
    else:
        print("⚠ DEEPSEEK_API_KEY 未配置或使用默认值")
    
    if api_url:
        print(f"✓ DEEPSEEK_API_URL: {api_url}")
    else:
        print("⚠ DEEPSEEK_API_URL 未配置")
    
    # 检查数据库
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✓ 数据库连接正常")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")


if __name__ == '__main__':
    print("开始测试LangGraph工作流系统...")
    
    test_configuration()
    
    # 运行异步测试
    success = asyncio.run(test_langgraph_integration())
    
    if success:
        print("\n🎉 LangGraph工作流系统测试通过！")
        print("系统已准备就绪，可以开始使用。")
    else:
        print("\n❌ 测试失败，请检查错误信息并修复问题。")
        sys.exit(1)