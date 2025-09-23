"""
提示词模块
包含各种AI代理的提示词模板
"""

from .code_explainer_prompts import CODE_EXPLAINER_PROMPTS
from .problem_solver_prompts import PROBLEM_SOLVER_PROMPTS
from .conversation_prompts import CONVERSATION_PROMPTS
from .code_analyzer_prompts import CODE_ANALYZER_PROMPTS
from .system_prompts import SYSTEM_PROMPTS

__all__ = [
    'CODE_EXPLAINER_PROMPTS',
    'PROBLEM_SOLVER_PROMPTS', 
    'CONVERSATION_PROMPTS',
    'CODE_ANALYZER_PROMPTS',
    'SYSTEM_PROMPTS'
]