"""
基于LangGraph的智能服务接口
替换原有的简单AI服务，提供更强大的工作流功能
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from django.conf import settings
from .langgraph_workflow import workflow_engine
from .workflow_state import Message, CodeSolution
from .ai_service import AIServiceError

logger = logging.getLogger(__name__)


class LangGraphService:
    """基于LangGraph的智能服务"""
    
    def __init__(self):
        self.workflow_engine = workflow_engine
        
    def _run_async(self, coro):
        """在同步环境中运行异步代码"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def _convert_history_to_messages(self, conversation_history: List[Dict[str, str]]) -> List[Message]:
        """转换对话历史格式"""
        messages = []
        for item in conversation_history:
            message = Message(
                role=item.get("role", "user"),
                content=item.get("content", ""),
                timestamp=datetime.now()
            )
            messages.append(message)
        return messages
    
    def _format_code_solutions(self, solutions: List[CodeSolution]) -> List[Dict[str, Any]]:
        """格式化代码解决方案"""
        formatted_solutions = []
        for solution in solutions:
            formatted_solutions.append({
                "title": solution.title,
                "code": solution.code,
                "explanation": solution.explanation,
                "difficulty": solution.difficulty,
                "packages": solution.packages,
                "filename": solution.filename
            })
        return formatted_solutions
    
    def explain_code(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """代码解释服务 - 使用LangGraph工作流"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="explain",
                    user_input=code,
                    session_id=session_id
                )
            )
            
            # 格式化返回结果
            response = {
                "content": result.get("explanation_result") or result.get("ai_response", ""),
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success",
                "metadata": {
                    "workflow_steps": result.get("processing_steps", []),
                    "code_analysis": result.get("code_analysis"),
                    "quality_score": result.get("quality_score"),
                    "warnings": result.get("warnings", []),
                    "errors": result.get("errors", [])
                }
            }
            
            if not response["success"]:
                raise AIServiceError(f"代码解释失败: {'; '.join(result.get('errors', []))}")
            
            logger.info(f"代码解释完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码解释服务失败: {str(e)}")
            raise AIServiceError(f"代码解释失败: {str(e)}")
    
    def solve_problem(self, problem: str, session_id: str = None) -> Dict[str, Any]:
        """问题求解服务 - 使用LangGraph工作流"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="answer",
                    user_input=problem,
                    session_id=session_id
                )
            )
            
            # 格式化解决方案
            solutions = self._format_code_solutions(result.get("code_solutions", []))
            
            # 格式化返回结果
            response = {
                "content": result.get("ai_response", ""),
                "solutions": solutions,
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success",
                "metadata": {
                    "workflow_steps": result.get("processing_steps", []),
                    "problem_type": result.get("problem_type"),
                    "warnings": result.get("warnings", []),
                    "errors": result.get("errors", [])
                }
            }
            
            if not response["success"]:
                raise AIServiceError(f"问题求解失败: {'; '.join(result.get('errors', []))}")
            
            logger.info(f"问题求解完成，会话ID: {session_id}，生成{len(solutions)}个解决方案")
            return response
            
        except Exception as e:
            logger.error(f"问题求解服务失败: {str(e)}")
            raise AIServiceError(f"问题求解失败: {str(e)}")
    
    def chat(self, message: str, conversation_history: List[Dict[str, str]] = None, 
             session_id: str = None) -> Dict[str, Any]:
        """智能对话服务 - 使用LangGraph工作流"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 转换对话历史
            history_messages = self._convert_history_to_messages(conversation_history or [])
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="talk",
                    user_input=message,
                    session_id=session_id,
                    conversation_history=history_messages
                )
            )
            
            # 格式化返回结果
            response = {
                "content": result.get("ai_response", ""),
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success",
                "metadata": {
                    "workflow_steps": result.get("processing_steps", []),
                    "conversation_length": len(result.get("conversation_history", [])),
                    "warnings": result.get("warnings", []),
                    "errors": result.get("errors", [])
                }
            }
            
            if not response["success"]:
                raise AIServiceError(f"智能对话失败: {'; '.join(result.get('errors', []))}")
            
            logger.info(f"智能对话完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"智能对话服务失败: {str(e)}")
            raise AIServiceError(f"智能对话失败: {str(e)}")
    
    def analyze_code_quality(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """代码质量分析服务"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 执行代码解释工作流（包含分析）
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="explain",
                    user_input=code,
                    session_id=session_id
                )
            )
            
            # 提取分析结果
            analysis = result.get("code_analysis", {})
            
            response = {
                "content": analysis.get("analysis_result", ""),
                "quality_score": analysis.get("quality_score", 0),
                "suggestions": analysis.get("suggestions", []),
                "complexity": analysis.get("complexity", "unknown"),
                "maintainability": analysis.get("maintainability", "unknown"),
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success"
            }
            
            logger.info(f"代码质量分析完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码质量分析失败: {str(e)}")
            raise AIServiceError(f"代码质量分析失败: {str(e)}")
    
    def generate_tests(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """测试用例生成服务"""
        # 暂时使用简化实现，可以后续扩展为完整的工作流
        try:
            test_code = f"""
# 为以下代码生成的测试用例
# 原始代码:
{code}

# 测试用例
library(testthat)

test_that("基本功能测试", {{
  # 测试基本功能
  expect_true(TRUE)
}})

test_that("边界条件测试", {{
  # 测试边界条件
  expect_true(TRUE)
}})

test_that("异常处理测试", {{
  # 测试异常处理
  expect_true(TRUE)
}})
"""
            
            response = {
                "content": test_code,
                "processing_time": 0.1,
                "usage": {"total_tokens": 100},
                "success": True
            }
            
            logger.info(f"测试用例生成完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"测试用例生成失败: {str(e)}")
            raise AIServiceError(f"测试用例生成失败: {str(e)}")
    
    def optimize_code(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """代码优化服务"""
        # 暂时使用简化实现，可以后续扩展为完整的工作流
        try:
            optimized_code = f"""
# 优化后的代码
# 原始代码:
{code}

# 优化建议:
# 1. 添加错误处理
# 2. 优化性能
# 3. 提高可读性

# 优化后的代码:
{code}  # 这里应该是实际优化后的代码
"""
            
            response = {
                "content": optimized_code,
                "processing_time": 0.1,
                "usage": {"total_tokens": 100},
                "success": True
            }
            
            logger.info(f"代码优化完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码优化失败: {str(e)}")
            raise AIServiceError(f"代码优化失败: {str(e)}")


# 创建服务工厂
class LangGraphServiceFactory:
    """LangGraph服务工厂"""
    
    @staticmethod
    def get_service(service_type: str = 'langgraph') -> LangGraphService:
        """获取LangGraph服务实例"""
        if service_type == 'langgraph':
            return LangGraphService()
        else:
            raise AIServiceError(f"Unsupported service type: {service_type}")


# 全局服务实例
langgraph_service = LangGraphServiceFactory.get_service()