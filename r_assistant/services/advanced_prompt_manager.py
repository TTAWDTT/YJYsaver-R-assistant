"""
高级提示词管理器
集成来自prompts文件夹的所有提示词模板
"""

from typing import Dict, Any, Optional
import os
import logging

# 导入各种提示词模板
try:
    # Django环境中的导入
    from prompts import (
        CODE_EXPLAINER_PROMPTS,
        PROBLEM_SOLVER_PROMPTS,
        CONVERSATION_PROMPTS,
        CODE_ANALYZER_PROMPTS,
        SYSTEM_PROMPTS
    )
except ImportError:
    # 开发环境中的导入
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from prompts import (
        CODE_EXPLAINER_PROMPTS,
        PROBLEM_SOLVER_PROMPTS,
        CONVERSATION_PROMPTS,
        CODE_ANALYZER_PROMPTS,
        SYSTEM_PROMPTS
    )

logger = logging.getLogger(__name__)


class AdvancedPromptManager:
    """高级提示词管理器"""
    
    def __init__(self):
        self.prompts = {
            'code_explainer': CODE_EXPLAINER_PROMPTS,
            'problem_solver': PROBLEM_SOLVER_PROMPTS,
            'conversation': CONVERSATION_PROMPTS,
            'code_analyzer': CODE_ANALYZER_PROMPTS,
            'system': SYSTEM_PROMPTS
        }
        
    def get_prompt(self, category: str, prompt_type: str, **kwargs) -> str:
        """
        获取指定类别和类型的提示词
        
        Args:
            category: 提示词类别 (code_explainer, problem_solver, etc.)
            prompt_type: 提示词类型 (system, user_template, etc.)
            **kwargs: 模板变量
            
        Returns:
            格式化后的提示词
        """
        try:
            if category not in self.prompts:
                logger.error(f"Unknown prompt category: {category}")
                return self._get_fallback_prompt(prompt_type)
                
            category_prompts = self.prompts[category]
            
            if prompt_type not in category_prompts:
                logger.error(f"Unknown prompt type '{prompt_type}' in category '{category}'")
                return self._get_fallback_prompt(prompt_type)
                
            prompt_template = category_prompts[prompt_type]
            
            # 格式化提示词模板
            if kwargs:
                return prompt_template.format(**kwargs)
            else:
                return prompt_template
                
        except Exception as e:
            logger.error(f"Error getting prompt: {e}")
            return self._get_fallback_prompt(prompt_type)
    
    def get_system_prompt(self, agent_type: str) -> str:
        """获取代理的系统提示词"""
        return self.get_prompt(agent_type, 'system')
    
    def get_user_prompt(self, agent_type: str, **kwargs) -> str:
        """获取用户交互提示词"""
        return self.get_prompt(agent_type, 'user_template', **kwargs)
    
    def _get_fallback_prompt(self, prompt_type: str) -> str:
        """获取后备提示词"""
        fallback_prompts = {
            'system': SYSTEM_PROMPTS['base_system'],
            'user_template': "用户请求：{message}\n\n请提供帮助。",
            'default': "我是你的R语言编程助手，请告诉我如何帮助你。"
        }
        
        return fallback_prompts.get(prompt_type, fallback_prompts['default'])
    
    def list_available_prompts(self) -> Dict[str, list]:
        """列出所有可用的提示词"""
        available = {}
        for category, prompts in self.prompts.items():
            available[category] = list(prompts.keys())
        return available
    
    def validate_prompts(self) -> Dict[str, Any]:
        """验证所有提示词模板"""
        validation_results = {
            'valid': [],
            'invalid': [],
            'warnings': []
        }
        
        for category, prompts in self.prompts.items():
            for prompt_type, prompt_template in prompts.items():
                try:
                    # 基本格式验证
                    if not isinstance(prompt_template, str):
                        validation_results['invalid'].append(
                            f"{category}.{prompt_type}: Not a string"
                        )
                        continue
                    
                    if len(prompt_template.strip()) == 0:
                        validation_results['invalid'].append(
                            f"{category}.{prompt_type}: Empty prompt"
                        )
                        continue
                    
                    # 检查模板变量格式
                    import re
                    template_vars = re.findall(r'\{(\w+)\}', prompt_template)
                    
                    validation_results['valid'].append(
                        f"{category}.{prompt_type}: OK (vars: {template_vars})"
                    )
                    
                except Exception as e:
                    validation_results['invalid'].append(
                        f"{category}.{prompt_type}: Error - {str(e)}"
                    )
        
        return validation_results
    
    def get_prompt_info(self, category: str, prompt_type: str) -> Dict[str, Any]:
        """获取提示词的详细信息"""
        if category not in self.prompts:
            return {'error': f'Category {category} not found'}
        
        if prompt_type not in self.prompts[category]:
            return {'error': f'Prompt type {prompt_type} not found in {category}'}
        
        prompt = self.prompts[category][prompt_type]
        
        # 分析模板变量
        import re
        template_vars = re.findall(r'\{(\w+)\}', prompt)
        
        return {
            'category': category,
            'type': prompt_type,
            'length': len(prompt),
            'template_variables': template_vars,
            'preview': prompt[:200] + '...' if len(prompt) > 200 else prompt
        }


# 创建全局提示词管理器实例
advanced_prompt_manager = AdvancedPromptManager()


# 向后兼容的PromptManager类
class PromptManager:
    """原有的PromptManager类，保持向后兼容"""
    
    @staticmethod
    def get_explain_prompt(code: str, additional_context: str = "") -> str:
        return advanced_prompt_manager.get_prompt(
            'code_explainer', 'user_template',
            code=code, additional_context=additional_context
        )
    
    @staticmethod
    def get_solve_prompt(problem_description: str, additional_requirements: str = "") -> str:
        return advanced_prompt_manager.get_prompt(
            'problem_solver', 'user_template',
            problem_description=problem_description, 
            additional_requirements=additional_requirements
        )
    
    @staticmethod
    def get_chat_prompt(message: str, conversation_context: str = "") -> str:
        return advanced_prompt_manager.get_prompt(
            'conversation', 'user_template',
            message=message, conversation_context=conversation_context
        )
    
    @staticmethod
    def get_system_prompt(agent_type: str = "base") -> str:
        if agent_type == "base":
            return advanced_prompt_manager.get_prompt('system', 'base_system')
        return advanced_prompt_manager.get_system_prompt(agent_type)