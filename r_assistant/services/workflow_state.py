"""
LangGraph工作流状态定义
定义所有工作流中使用的状态结构
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodeSolution(BaseModel):
    """代码解决方案模型"""
    title: str = Field(..., description="解决方案标题")
    code: str = Field(..., description="R代码")
    explanation: str = Field(..., description="代码解释")
    difficulty: str = Field(default="basic", description="难度级别: basic/intermediate/advanced")
    packages: List[str] = Field(default_factory=list, description="所需R包")
    filename: str = Field(default="solution.R", description="建议文件名")


class WorkflowState(TypedDict):
    """LangGraph工作流状态"""
    # 基础信息
    session_id: str
    request_id: str
    request_type: str  # explain, answer, talk
    
    # 用户输入
    user_input: str
    original_code: Optional[str]
    problem_description: Optional[str]
    
    # 对话历史
    conversation_history: List[Message]
    
    # 处理结果
    ai_response: Optional[str]
    code_solutions: List[CodeSolution]
    explanation_result: Optional[str]
    
    # 分析结果
    code_analysis: Optional[Dict[str, Any]]
    quality_score: Optional[float]
    complexity_analysis: Optional[Dict[str, Any]]
    
    # 元数据
    processing_steps: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    total_tokens: int
    
    # 错误处理
    errors: List[str]
    warnings: List[str]
    
    # 工作流控制
    next_step: Optional[str]
    workflow_complete: bool


class AgentConfig(BaseModel):
    """代理配置"""
    name: str
    role: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 4000
    model: str = "deepseek-chat"


class WorkflowConfig(BaseModel):
    """工作流配置"""
    workflow_type: str
    agents: List[AgentConfig]
    max_iterations: int = 10
    timeout_seconds: int = 300
    enable_parallel_processing: bool = False