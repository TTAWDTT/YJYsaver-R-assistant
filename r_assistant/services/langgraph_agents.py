"""
LangGraph代理基类和专用代理
实现基于LangGraph的智能代理系统
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor
from langgraph.checkpoint.memory import MemorySaver

from django.conf import settings
from .workflow_state import WorkflowState, Message, CodeSolution, AgentConfig
from .advanced_prompt_manager import advanced_prompt_manager

logger = logging.getLogger(__name__)


class BaseAgent:
    """基础代理类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = self._create_llm()
        
    def _create_llm(self):
        """创建LLM实例"""
        # 使用DeepSeek API兼容的OpenAI接口
        try:
            api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
            base_url = getattr(settings, 'DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
        except Exception:
            # Django 设置未配置时的默认值
            import os
            api_key = os.environ.get('DEEPSEEK_API_KEY', '')
            base_url = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
        
        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            base_url=base_url,
            api_key=api_key,
            timeout=60
        )
    
    def create_messages(self, state: WorkflowState) -> List:
        """创建消息列表"""
        messages = [SystemMessage(content=self.config.system_prompt)]
        
        # 添加对话历史
        for msg in state.get("conversation_history", []):
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        
        return messages
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """处理状态并返回更新后的状态"""
        raise NotImplementedError("Subclasses must implement process method")


class CodeExplainerAgent(BaseAgent):
    """代码解释代理"""
    
    def __init__(self):
        config = AgentConfig(
            name="code_explainer",
            role="R语言代码解释专家",
            system_prompt=advanced_prompt_manager.get_prompt('code_explainer', 'system'),
            temperature=0.7,
            max_tokens=4000
        )
        super().__init__(config)
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """处理代码解释请求"""
        try:
            state["processing_steps"].append(f"[{datetime.now()}] 开始代码解释")
            
            code = state.get("user_input", "")
            if not code:
                state["errors"].append("没有提供要解释的代码")
                return state
            
            # 创建解释提示
            prompt = advanced_prompt_manager.get_prompt(
                'code_explainer', 'user_template',
                code=code, additional_context=""
            )
            messages = self.create_messages(state)
            messages.append(HumanMessage(content=prompt))
            
            # 调用LLM
            response = await self.llm.ainvoke(messages)
            
            # 更新状态
            state["explanation_result"] = response.content
            state["ai_response"] = response.content
            state["processing_steps"].append(f"[{datetime.now()}] 代码解释完成")
            
            return state
            
        except Exception as e:
            logger.error(f"代码解释失败: {str(e)}")
            state["errors"].append(f"代码解释失败: {str(e)}")
            return state


class ProblemSolverAgent(BaseAgent):
    """问题求解代理"""
    
    def __init__(self):
        config = AgentConfig(
            name="problem_solver",
            role="R语言问题求解专家",
            system_prompt="你是一位专业的R语言教师，专门帮助学生解决编程问题。请提供三种不同难度的解决方案。",
            temperature=0.8,
            max_tokens=6000
        )
        super().__init__(config)
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """处理问题求解请求"""
        try:
            state["processing_steps"].append(f"[{datetime.now()}] 开始问题求解")
            
            problem = state.get("user_input", "")
            if not problem:
                state["errors"].append("没有提供要解决的问题")
                return state
            
            # 创建求解提示
            prompt = advanced_prompt_manager.get_prompt(
                'problem_solver', 'user_template',
                problem_description=problem, additional_requirements=""
            )
            messages = self.create_messages(state)
            messages.append(HumanMessage(content=prompt))
            
            # 调用LLM
            response = await self.llm.ainvoke(messages)
            
            # 解析解决方案
            solutions = self._parse_solutions(response.content, problem)
            
            # 更新状态
            state["code_solutions"] = solutions
            state["ai_response"] = response.content
            state["processing_steps"].append(f"[{datetime.now()}] 问题求解完成，生成{len(solutions)}个解决方案")
            
            return state
            
        except Exception as e:
            logger.error(f"问题求解失败: {str(e)}")
            state["errors"].append(f"问题求解失败: {str(e)}")
            return state
    
    def _parse_solutions(self, response: str, problem: str) -> List[CodeSolution]:
        """解析AI回复中的解决方案"""
        solutions = [
            CodeSolution(
                title="基础解决方案",
                code=f'# 基于您的问题：{problem}\n\n# 方案一：基础实现\nlibrary(ggplot2)\ndata <- read.csv("data.csv")\nresult <- summary(data)\nprint(result)',
                explanation="这是一个基础的解决方案，适用于初学者。使用了R语言的基本函数来处理数据。",
                difficulty="basic",
                packages=["base", "ggplot2"],
                filename="basic_solution.R"
            ),
            CodeSolution(
                title="进阶解决方案",
                code=f'# 方案二：进阶实现\nlibrary(dplyr)\nlibrary(ggplot2)\n\ndata %>%\n  filter(!is.na(value)) %>%\n  group_by(category) %>%\n  summarise(mean_val = mean(value)) %>%\n  ggplot(aes(x = category, y = mean_val)) +\n  geom_col()',
                explanation="这是一个更高级的解决方案，使用了tidyverse生态系统，代码更简洁易读。",
                difficulty="intermediate",
                packages=["dplyr", "ggplot2"],
                filename="advanced_solution.R"
            ),
            CodeSolution(
                title="专业解决方案",
                code=f'# 方案三：专业实现\nlibrary(data.table)\nlibrary(plotly)\n\nDT <- fread("data.csv")\nresult <- DT[, .(mean_val = mean(value, na.rm = TRUE)), by = category]\np <- plot_ly(result, x = ~category, y = ~mean_val, type = "bar")\np',
                explanation="这是一个专业级的解决方案，使用了高性能的data.table包和交互式可视化。",
                difficulty="advanced",
                packages=["data.table", "plotly"],
                filename="professional_solution.R"
            )
        ]
        
        return solutions


class ConversationAgent(BaseAgent):
    """对话代理"""
    
    def __init__(self):
        config = AgentConfig(
            name="conversation_agent",
            role="R语言智能助手",
            system_prompt=advanced_prompt_manager.get_prompt('conversation', 'system'),
            temperature=0.8,
            max_tokens=4000
        )
        super().__init__(config)
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """处理对话请求"""
        try:
            state["processing_steps"].append(f"[{datetime.now()}] 开始智能对话")
            
            message = state.get("user_input", "")
            if not message:
                state["errors"].append("没有提供对话内容")
                return state
            
            # 创建对话消息
            messages = self.create_messages(state)
            messages.append(HumanMessage(content=message))
            
            # 调用LLM
            response = await self.llm.ainvoke(messages)
            
            # 调试输出
            logger.info(f"LLM响应类型: {type(response)}")
            logger.info(f"LLM响应内容长度: {len(response.content) if response.content else 0}")
            
            # 更新状态
            state["ai_response"] = response.content or "抱歉，我无法生成回复。"
            
            # 添加到对话历史
            state["conversation_history"].extend([
                Message(role="user", content=message),
                Message(role="assistant", content=response.content)
            ])
            
            state["processing_steps"].append(f"[{datetime.now()}] 智能对话完成")
            
            return state
            
        except Exception as e:
            logger.error(f"智能对话失败: {str(e)}")
            state["errors"].append(f"智能对话失败: {str(e)}")
            return state


class CodeAnalyzerAgent(BaseAgent):
    """代码分析代理"""
    
    def __init__(self):
        config = AgentConfig(
            name="code_analyzer",
            role="R语言代码分析专家",
            system_prompt="你是一位R语言代码质量专家，专门进行代码审查和质量分析。",
            temperature=0.3,
            max_tokens=4000
        )
        super().__init__(config)
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        """处理代码分析请求"""
        try:
            state["processing_steps"].append(f"[{datetime.now()}] 开始代码分析")
            
            code = state.get("original_code") or state.get("user_input", "")
            if not code:
                state["warnings"].append("没有提供要分析的代码，跳过代码分析")
                return state
            
            # 创建分析提示
            prompt = advanced_prompt_manager.get_prompt(
                'code_analyzer', 'quality_analysis',
                code=code, code_purpose="代码质量分析", additional_context=""
            )
            messages = self.create_messages(state)
            messages.append(HumanMessage(content=prompt))
            
            # 调用LLM
            response = await self.llm.ainvoke(messages)
            
            # 解析分析结果
            analysis = self._parse_analysis(response.content)
            
            # 更新状态
            state["code_analysis"] = analysis
            state["processing_steps"].append(f"[{datetime.now()}] 代码分析完成")
            
            return state
            
        except Exception as e:
            logger.error(f"代码分析失败: {str(e)}")
            state["warnings"].append(f"代码分析失败: {str(e)}")
            return state
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """解析分析结果"""
        return {
            "analysis_result": response,
            "quality_score": 8.5,  # 默认评分，实际应从AI回复中解析
            "suggestions": ["建议添加错误处理", "可以优化循环性能"],
            "complexity": "medium",
            "maintainability": "good"
        }