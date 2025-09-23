"""
LangGraph工作流引擎
实现基于LangGraph的智能工作流系统
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from .workflow_state import WorkflowState, Message, WorkflowConfig
from .langgraph_agents import (
    CodeExplainerAgent, 
    ProblemSolverAgent, 
    ConversationAgent, 
    CodeAnalyzerAgent
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """LangGraph工作流引擎"""
    
    def __init__(self):
        self.agents = {
            "code_explainer": CodeExplainerAgent(),
            "problem_solver": ProblemSolverAgent(),
            "conversation_agent": ConversationAgent(),
            "code_analyzer": CodeAnalyzerAgent(),
        }
        self.memory = MemorySaver()
        self.workflows = {}
        self._build_workflows()
    
    def _build_workflows(self):
        """构建不同类型的工作流"""
        
        # 代码解释工作流
        explain_workflow = StateGraph(WorkflowState)
        explain_workflow.add_node("analyze_code", self._analyze_code_node)
        explain_workflow.add_node("explain_code", self._explain_code_node)
        explain_workflow.add_node("finalize", self._finalize_node)
        
        explain_workflow.add_edge(START, "analyze_code")
        explain_workflow.add_edge("analyze_code", "explain_code")
        explain_workflow.add_edge("explain_code", "finalize")
        explain_workflow.add_edge("finalize", END)
        
        self.workflows["explain"] = explain_workflow.compile(checkpointer=self.memory)
        
        # 问题求解工作流
        answer_workflow = StateGraph(WorkflowState)
        answer_workflow.add_node("analyze_problem", self._analyze_problem_node)
        answer_workflow.add_node("solve_problem", self._solve_problem_node)
        answer_workflow.add_node("validate_solutions", self._validate_solutions_node)
        answer_workflow.add_node("finalize", self._finalize_node)
        
        answer_workflow.add_edge(START, "analyze_problem")
        answer_workflow.add_edge("analyze_problem", "solve_problem")
        answer_workflow.add_edge("solve_problem", "validate_solutions")
        answer_workflow.add_edge("validate_solutions", "finalize")
        answer_workflow.add_edge("finalize", END)
        
        self.workflows["answer"] = answer_workflow.compile(checkpointer=self.memory)
        
        # 智能对话工作流
        talk_workflow = StateGraph(WorkflowState)
        talk_workflow.add_node("conversation", self._conversation_node)
        talk_workflow.add_node("context_enhancement", self._context_enhancement_node)
        talk_workflow.add_node("finalize", self._finalize_node)
        
        talk_workflow.add_edge(START, "conversation")
        talk_workflow.add_edge("conversation", "context_enhancement")
        talk_workflow.add_edge("context_enhancement", "finalize")
        talk_workflow.add_edge("finalize", END)
        
        self.workflows["talk"] = talk_workflow.compile(checkpointer=self.memory)
    
    async def execute_workflow(self, request_type: str, user_input: str, 
                             session_id: str, conversation_history: List[Message] = None) -> WorkflowState:
        """执行工作流"""
        
        if request_type not in self.workflows:
            raise ValueError(f"Unsupported workflow type: {request_type}")
        
        # 初始化状态
        initial_state = WorkflowState(
            session_id=session_id,
            request_id=str(uuid.uuid4()),
            request_type=request_type,
            user_input=user_input,
            original_code=user_input if request_type == "explain" else None,
            problem_description=user_input if request_type == "answer" else None,
            conversation_history=conversation_history or [],
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
        
        try:
            logger.info(f"开始执行{request_type}工作流，会话ID: {session_id}")
            
            # 执行工作流
            workflow = self.workflows[request_type]
            config = {"configurable": {"thread_id": session_id}}
            
            final_state = await workflow.ainvoke(initial_state, config)
            
            # 标记完成
            final_state["end_time"] = datetime.now()
            final_state["workflow_complete"] = True
            
            logger.info(f"{request_type}工作流执行完成，会话ID: {session_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            initial_state["errors"].append(f"工作流执行失败: {str(e)}")
            initial_state["end_time"] = datetime.now()
            return initial_state
    
    # 工作流节点实现
    
    async def _analyze_code_node(self, state: WorkflowState) -> WorkflowState:
        """代码分析节点"""
        return await self.agents["code_analyzer"].process(state)
    
    async def _explain_code_node(self, state: WorkflowState) -> WorkflowState:
        """代码解释节点"""
        return await self.agents["code_explainer"].process(state)
    
    async def _analyze_problem_node(self, state: WorkflowState) -> WorkflowState:
        """问题分析节点"""
        state["processing_steps"].append(f"[{datetime.now()}] 开始问题分析")
        
        # 这里可以添加问题分析逻辑
        problem = state.get("user_input", "")
        
        # 简单的问题分类
        if any(keyword in problem.lower() for keyword in ["画图", "绘图", "plot", "graph"]):
            state["problem_type"] = "visualization"
        elif any(keyword in problem.lower() for keyword in ["统计", "分析", "analysis"]):
            state["problem_type"] = "statistics"
        elif any(keyword in problem.lower() for keyword in ["数据处理", "清洗", "clean"]):
            state["problem_type"] = "data_processing"
        else:
            state["problem_type"] = "general"
        
        state["processing_steps"].append(f"[{datetime.now()}] 问题分析完成，类型: {state.get('problem_type', 'unknown')}")
        return state
    
    async def _solve_problem_node(self, state: WorkflowState) -> WorkflowState:
        """问题求解节点"""
        return await self.agents["problem_solver"].process(state)
    
    async def _validate_solutions_node(self, state: WorkflowState) -> WorkflowState:
        """解决方案验证节点"""
        state["processing_steps"].append(f"[{datetime.now()}] 开始解决方案验证")
        
        solutions = state.get("code_solutions", [])
        
        # 验证解决方案
        for i, solution in enumerate(solutions):
            if len(solution.code) < 10:
                state["warnings"].append(f"解决方案{i+1}代码过短，可能不完整")
            
            if not solution.packages:
                state["warnings"].append(f"解决方案{i+1}未指定所需R包")
        
        state["processing_steps"].append(f"[{datetime.now()}] 解决方案验证完成")
        return state
    
    async def _conversation_node(self, state: WorkflowState) -> WorkflowState:
        """对话节点"""
        return await self.agents["conversation_agent"].process(state)
    
    async def _context_enhancement_node(self, state: WorkflowState) -> WorkflowState:
        """上下文增强节点"""
        state["processing_steps"].append(f"[{datetime.now()}] 开始上下文增强")
        
        # 这里可以添加上下文增强逻辑，比如：
        # - 检查是否需要补充信息
        # - 提供相关建议
        # - 添加学习资源链接等
        
        ai_response = state.get("ai_response", "")
        if ai_response and len(ai_response) < 50:
            state["warnings"].append("AI回复较短，可能需要更多上下文")
        
        state["processing_steps"].append(f"[{datetime.now()}] 上下文增强完成")
        return state
    
    async def _finalize_node(self, state: WorkflowState) -> WorkflowState:
        """最终化节点"""
        logger.info("执行 finalize 节点")
        state["processing_steps"].append(f"[{datetime.now()}] 开始最终化处理")
        
        # 设置结束时间（如果未设置）
        if not state.get("end_time"):
            state["end_time"] = datetime.now()
        
        # 计算总处理时间
        if state.get("start_time") and state.get("end_time"):
            processing_time = (state["end_time"] - state["start_time"]).total_seconds()
            state["processing_time"] = processing_time
        
        # 生成摘要
        if state.get("errors"):
            state["status"] = "error"
            state["summary"] = f"处理失败: {'; '.join(state['errors'])}"
            logger.info("设置状态为 error")
        elif state.get("warnings"):
            state["status"] = "warning"
            state["summary"] = f"处理完成但有警告: {'; '.join(state['warnings'])}"
            logger.info("设置状态为 warning")
        else:
            state["status"] = "success"
            state["summary"] = "处理成功完成"
            logger.info("设置状态为 success")
        
        state["processing_steps"].append(f"[{datetime.now()}] 最终化处理完成")
        logger.info(f"finalize完成，最终状态: {state.get('status')}")
        return state


# 全局工作流引擎实例
workflow_engine = WorkflowEngine()