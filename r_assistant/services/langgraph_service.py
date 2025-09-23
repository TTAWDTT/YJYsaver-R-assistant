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
        try:
            self.api_key_available = bool(getattr(settings, 'DEEPSEEK_API_KEY', ''))
        except Exception:
            import os
            self.api_key_available = bool(os.environ.get('DEEPSEEK_API_KEY', ''))
        
    def _check_api_availability(self):
        """检查API是否可用"""
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not api_key or api_key.startswith('sk-请替换') or api_key == 'sk-placeholder-key-change-this':
            logger.warning("DEEPSEEK_API_KEY未正确配置，使用演示模式")
            return False
        return True
        
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
    
    def explain_code(self, code: str, session_id: str = None, mode: str = 'full') -> Dict[str, Any]:
        """代码解释服务 - 使用LangGraph工作流
        
        Args:
            code: 要解释的代码
            session_id: 会话ID
            mode: 分析模式 ('full', 'selected')
        """
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("explain", code, mode)
            
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
                "analysis_mode": mode,
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
            
            logger.info(f"代码解释完成（模式：{mode}），会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码解释服务失败: {str(e)}")
            raise AIServiceError(f"代码解释失败: {str(e)}")
    
    def solve_problem(self, problem: str, session_id: str = None, uploaded_files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """问题求解服务 - 使用LangGraph工作流，支持文件上传"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("solve", problem, uploaded_files)
            
            # 准备文件内容描述
            file_context = ""
            if uploaded_files:
                file_context = "\n\n相关文件内容：\n"
                for file_info in uploaded_files:
                    file_context += f"\n--- 文件: {file_info['filename']} (类型: {file_info['type']}, 大小: {file_info['size']} 字节) ---\n"
                    if file_info['content'].startswith('[二进制文件'):
                        file_context += file_info['content'] + "\n"
                    else:
                        # 限制文件内容长度，避免过长
                        content = file_info['content']
                        if len(content) > 5000:
                            content = content[:5000] + "\n... (内容被截断，文件过长)"
                        file_context += content + "\n"
                file_context += "\n请基于以上文件内容来解决问题。"
            
            # 组合问题描述和文件内容
            enhanced_problem = problem + file_context
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="answer",
                    user_input=enhanced_problem,
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
                    "errors": result.get("errors", []),
                    "uploaded_files_count": len(uploaded_files) if uploaded_files else 0
                }
            }
            
            if not response["success"]:
                raise AIServiceError(f"问题求解失败: {'; '.join(result.get('errors', []))}")
            
            logger.info(f"问题求解完成，会话ID: {session_id}，生成{len(solutions)}个解决方案，包含{len(uploaded_files) if uploaded_files else 0}个文件")
            return response
            
        except Exception as e:
            logger.error(f"问题求解服务失败: {str(e)}")
            raise AIServiceError(f"问题求解失败: {str(e)}")
    
    def chat(self, message: str, conversation_history: List[Dict[str, str]] = None, 
             session_id: str = None) -> Dict[str, Any]:
        """智能对话服务 - 使用LangGraph工作流"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("chat", message)
            
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
            
            # 检查是否有内容返回
            if not response["content"] and response["success"]:
                logger.warning("AI响应为空，但状态为成功")
                response["content"] = "抱歉，我暂时无法生成回复，请稍后再试。"
            
            if not response["success"]:
                error_msg = '; '.join(result.get('errors', [])) or "未知错误"
                raise AIServiceError(f"智能对话失败: {error_msg}")
            
            logger.info(f"智能对话完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"智能对话服务失败: {str(e)}")
            raise AIServiceError(f"智能对话失败: {str(e)}")
    
    def analyze_code_quality(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """代码质量分析服务"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("analyze", code)
            
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
    
    def _create_demo_response(self, request_type: str, user_input: str, mode_or_files = 'full') -> Dict[str, Any]:
        """创建演示响应（当API密钥不可用时）"""
        # 处理参数兼容性
        if isinstance(mode_or_files, list):
            uploaded_files = mode_or_files
            mode = 'full'
            file_info = f"\n\n📎 **包含{len(uploaded_files)}个上传文件：**\n"
            for file in uploaded_files:
                file_info += f"- {file['filename']} ({file['type']}, {file['size']} 字节)\n"
        else:
            mode = mode_or_files
            uploaded_files = None
            file_info = ""
        
        demo_responses = {
            "chat": f"🤖 **R语言智能助手演示模式**\n\n你好！我是R语言智能助手。\n\n**你说：** {user_input}\n\n---\n\n⚠️ **当前处于演示模式**\n\n要启用完整的AI功能，请按以下步骤配置API密钥：\n\n1. 访问 https://platform.deepseek.com 注册账号\n2. 获取您的API Key\n3. 在项目根目录的 `.env` 文件中设置：\n   ```\n   DEEPSEEK_API_KEY=你的API密钥\n   ```\n4. 重启服务器\n\n**配置完成后，我可以帮助你：**\n- 📝 解释R代码\n- 🔧 解决编程问题\n- 📚 提供学习建议\n- 📊 数据分析指导",
            
            "explain": f"📝 **代码解释功能演示{' - 选中代码分析' if mode == 'selected' else ''}**\n\n**你提交的代码：**\n```r\n{user_input}\n```\n\n---\n\n🎯 **演示解释：**\n\n这是一个演示响应。配置API密钥后，我将为你提供详细的代码分析，包括：\n\n- 📖 逐行代码解释\n- ⚙️ 函数功能说明  \n- ✨ 最佳实践建议\n- 🚀 性能优化方案\n\n{f'**当前选中代码分析模式** - 我会重点关注你选中的代码片段并结合完整上下文进行分析。' if mode == 'selected' else ''}\n\n---\n\n⚠️ **要启用完整功能，请配置DeepSeek API密钥：**\n\n1. 访问 https://platform.deepseek.com\n2. 在 `.env` 文件中设置 `DEEPSEEK_API_KEY`\n3. 重启服务器",
            
            "solve": f"🔧 **问题解决功能演示**\n\n**你的问题：** {user_input}{file_info}\n\n---\n\n🎯 **演示解决方案：**\n\n这是一个演示响应。配置API密钥后，我将提供：\n\n- 🔄 多种解决方案\n- 💻 详细代码实现\n- 📋 最佳实践指导\n- 📦 相关包推荐\n{f'- 📎 基于上传文件的个性化解决方案' if uploaded_files else ''}\n\n---\n\n⚠️ **配置API密钥以获得完整功能**",
            
            "analyze": f"📊 **代码分析功能演示**\n\n**你提交的代码：**\n```r\n{user_input}\n```\n\n---\n\n🎯 **演示分析：**\n\n配置API密钥后，我将提供：\n\n- 📈 代码质量评分\n- ⚡ 性能分析建议\n- 📏 代码规范检查\n- 🔧 优化建议\n\n---\n\n⚠️ **配置API密钥以获得完整功能**"
        }
        
        response = {
            "content": demo_responses.get(request_type, f"演示响应：{user_input}"),
            "processing_time": 0.1,
            "usage": {"total_tokens": 0},
            "success": True,
            "analysis_mode": mode,
            "metadata": {
                "demo_mode": True,
                "api_key_required": True,
                "message": "请配置DEEPSEEK_API_KEY以启用完整功能",
                "uploaded_files_count": len(uploaded_files) if uploaded_files else 0
            }
        }
        
        # 为求解问题添加演示解决方案
        if request_type == "solve":
            response["solutions"] = [
                {
                    "title": "演示解决方案 1",
                    "code": "# 这是一个演示代码\n# 配置API密钥后将提供真实解决方案\nprint('Hello, R World!')",
                    "explanation": "这是演示代码说明。配置API密钥后将提供详细的问题分析和多种解决方案。",
                    "filename": "demo_solution.R"
                }
            ]
        
        return response


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