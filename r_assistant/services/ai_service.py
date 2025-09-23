"""
AI服务接口
与DeepSeek API进行交互的服务层
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from .prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常类"""
    pass


class DeepSeekService:
    """DeepSeek API服务类"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        self.default_model = 'deepseek-chat'
        
        if not self.api_key or self.api_key == 'sk-placeholder-key-change-this':
            logger.warning("DeepSeek API key not configured properly. Please set DEEPSEEK_API_KEY in .env file.")
    
    def _make_request(self, messages: List[Dict[str, str]], 
                     model: str = None, 
                     temperature: float = 0.7,
                     max_tokens: int = 4000,
                     **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        
        # 检查API key是否已配置
        if not self.api_key or self.api_key == 'sk-placeholder-key-change-this':
            raise AIServiceError("DeepSeek API key not configured. Please set DEEPSEEK_API_KEY in .env file.")
        
        payload = {
            'model': model or self.default_model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            **kwargs
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            processing_time = time.time() - start_time
            
            response.raise_for_status()
            result = response.json()
            
            logger.info("DeepSeek API call successful. Time: %.2fs", processing_time)
            
            return {
                'content': result['choices'][0]['message']['content'],
                'processing_time': processing_time,
                'usage': result.get('usage', {}),
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            logger.error("DeepSeek API request failed: %s", str(e))
            raise AIServiceError(f"API request failed: {str(e)}")
        except KeyError as e:
            logger.error("Unexpected API response format: %s", str(e))
            raise AIServiceError(f"Invalid API response format: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in DeepSeek API call: %s", str(e))
            raise AIServiceError(f"Unexpected error: {str(e)}")
    
    def explain_code(self, code: str) -> Dict[str, Any]:
        """代码解释服务"""
        prompt = PromptManager.get_explain_prompt(code)
        messages = [
            {"role": "system", "content": PromptManager.get_talk_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self._make_request(messages, temperature=0.7)
            logger.info("Code explanation completed successfully")
            return result
        except Exception as e:
            logger.error("Code explanation failed: %s", str(e))
            raise
    
    def solve_problem(self, problem: str) -> Dict[str, Any]:
        """作业求解服务"""
        prompt = PromptManager.get_answer_prompt(problem)
        messages = [
            {"role": "system", "content": "你是一位专业的R语言教师，专门帮助学生解决编程问题。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self._make_request(messages, temperature=0.8, max_tokens=6000)
            logger.info("Problem solving completed successfully")
            return result
        except Exception as e:
            logger.error("Problem solving failed: %s", str(e))
            raise
    
    def chat(self, message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """智能对话服务"""
        messages = [{"role": "system", "content": PromptManager.get_talk_prompt()}]
        
        # 添加对话历史
        if conversation_history:
            # 限制历史记录长度，避免超出token限制
            recent_history = conversation_history[-10:]  # 保留最近10轮对话
            messages.extend(recent_history)
        
        messages.append({"role": "user", "content": message})
        
        try:
            result = self._make_request(messages, temperature=0.8)
            logger.info("Chat response completed successfully")
            return result
        except Exception as e:
            logger.error("Chat failed: %s", str(e))
            raise
    
    def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """代码质量分析服务"""
        prompt = PromptManager.get_code_quality_prompt(code)
        messages = [
            {"role": "system", "content": "你是一位R语言代码质量专家，专门进行代码审查和质量分析。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self._make_request(messages, temperature=0.3)  # 较低温度确保客观分析
            logger.info("Code quality analysis completed successfully")
            return result
        except Exception as e:
            logger.error("Code quality analysis failed: %s", str(e))
            raise
    
    def generate_tests(self, code: str) -> Dict[str, Any]:
        """测试用例生成服务"""
        prompt = PromptManager.get_test_generation_prompt(code)
        messages = [
            {"role": "system", "content": "你是一位R语言测试专家，专门编写全面的测试用例。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self._make_request(messages, temperature=0.5)
            logger.info("Test generation completed successfully")
            return result
        except Exception as e:
            logger.error("Test generation failed: %s", str(e))
            raise
    
    def optimize_code(self, code: str) -> Dict[str, Any]:
        """代码优化服务"""
        prompt = PromptManager.get_optimization_prompt(code)
        messages = [
            {"role": "system", "content": "你是一位R语言性能优化专家，专门进行代码优化和改进。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            result = self._make_request(messages, temperature=0.4)
            logger.info("Code optimization completed successfully")
            return result
        except Exception as e:
            logger.error("Code optimization failed: %s", str(e))
            raise


class AIServiceFactory:
    """AI服务工厂类"""
    
    @staticmethod
    def get_service(service_type: str = 'deepseek') -> DeepSeekService:
        """获取AI服务实例"""
        if service_type == 'deepseek':
            return DeepSeekService()
        else:
            raise AIServiceError(f"Unsupported service type: {service_type}")


# 全局服务实例
ai_service = AIServiceFactory.get_service()