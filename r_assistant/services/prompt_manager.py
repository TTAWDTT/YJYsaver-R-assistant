"""
提示词管理器
集中管理所有AI提示词模板 - 使用新的模块化提示词系统
"""

from .advanced_prompt_manager import advanced_prompt_manager


class PromptManager:
    """提示词管理器类 - 重构以使用新的提示词系统"""
    
    @staticmethod
    def get_explain_prompt(code: str, additional_context: str = "") -> str:
        """获取代码解释提示词"""
        return advanced_prompt_manager.get_prompt(
            'code_explainer', 'user_template',
            code=code, 
            additional_context=additional_context
        )
    
    @staticmethod
    def get_answer_prompt(problem: str, additional_requirements: str = "") -> str:
        """获取作业求解提示词"""
        return advanced_prompt_manager.get_prompt(
            'problem_solver', 'user_template',
            problem_description=problem,
            additional_requirements=additional_requirements
        )
    
    @staticmethod
    def get_talk_prompt(message: str, conversation_context: str = "") -> str:
        """获取对话提示词"""
        return advanced_prompt_manager.get_prompt(
            'conversation', 'user_template',
            message=message,
            conversation_context=conversation_context
        )
    
    @staticmethod
    def get_system_prompt(agent_type: str = "base") -> str:
        """获取系统提示词"""
        if agent_type == "base":
            return advanced_prompt_manager.get_prompt('system', 'base_system')
        return advanced_prompt_manager.get_system_prompt(agent_type)
    
    @staticmethod
    def get_analysis_prompt(code: str, analysis_type: str = "quality") -> str:
        """获取代码分析提示词"""
        prompt_map = {
            'quality': 'quality_analysis',
            'performance': 'performance_analysis', 
            'style': 'style_check',
            'security': 'security_analysis'
        }
        
        prompt_type = prompt_map.get(analysis_type, 'quality_analysis')
        
        return advanced_prompt_manager.get_prompt(
            'code_analyzer', prompt_type,
            code=code,
            code_purpose="代码分析",
            additional_context=""
        )
    
    @staticmethod
    def get_error_explanation_prompt(code: str, error_msg: str) -> str:
        """获取错误解释提示词"""
        return advanced_prompt_manager.get_prompt(
            'code_explainer', 'error_explanation',
            code=code,
            error_msg=error_msg
        )
    
    @staticmethod
    def get_data_analysis_prompt(data_description: str, analysis_goal: str, expected_output: str = "") -> str:
        """获取数据分析提示词"""
        return advanced_prompt_manager.get_prompt(
            'problem_solver', 'data_analysis_template',
            data_description=data_description,
            analysis_goal=analysis_goal,
            expected_output=expected_output,
            additional_context=""
        )
    
    @staticmethod
    def get_visualization_prompt(data_features: str, chart_type: str = "自动选择", visualization_goal: str = "") -> str:
        """获取可视化提示词"""
        return advanced_prompt_manager.get_prompt(
            'problem_solver', 'visualization_request',
            data_features=data_features,
            chart_type=chart_type,
            visualization_goal=visualization_goal,
            style_preferences=""
        )
    
    # 新增的高级功能方法
    @staticmethod
    def get_available_prompts() -> dict:
        """获取所有可用的提示词类型"""
        return advanced_prompt_manager.list_available_prompts()
    
    @staticmethod
    def validate_all_prompts() -> dict:
        """验证所有提示词模板"""
        return advanced_prompt_manager.validate_prompts()
    
    @staticmethod
    def get_prompt_info(category: str, prompt_type: str) -> dict:
        """获取特定提示词的详细信息"""
        return advanced_prompt_manager.get_prompt_info(category, prompt_type)
    
    @staticmethod
    def get_custom_prompt(category: str, prompt_type: str, **kwargs) -> str:
        """获取自定义提示词"""
        return advanced_prompt_manager.get_prompt(category, prompt_type, **kwargs)


# 兼容性别名，支持旧代码
def get_explain_prompt(code: str) -> str:
    """向后兼容的函数"""
    return PromptManager.get_explain_prompt(code)

def get_answer_prompt(problem: str) -> str:
    """向后兼容的函数"""
    return PromptManager.get_answer_prompt(problem)

def get_talk_prompt() -> str:
    """向后兼容的函数"""
    return advanced_prompt_manager.get_prompt('conversation', 'greeting')

def get_code_quality_prompt(code: str) -> str:
    """向后兼容的函数"""
    return PromptManager.get_analysis_prompt(code, 'quality')