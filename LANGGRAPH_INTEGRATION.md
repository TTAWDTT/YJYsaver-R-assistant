# LangGraph工作流系统集成指南

## 概述

本项目已成功集成LangGraph工作流框架，将原有的简单AI服务升级为基于状态图的智能代理工作流系统。LangGraph提供了更强大的状态管理、工作流控制和扩展能力。

## 新架构特性

### 🚀 核心优势

1. **状态化工作流**: 使用LangGraph的状态图管理复杂的处理流程
2. **多代理协作**: 不同专业化代理协同处理任务
3. **可观测性**: 完整的工作流执行跟踪和监控
4. **扩展性**: 易于添加新的代理和工作流节点
5. **容错性**: 更好的错误处理和重试机制

### 🏗️ 架构组件

```
services/
├── workflow_state.py      # 工作流状态定义
├── langgraph_agents.py    # 专业化代理实现
├── langgraph_workflow.py  # 工作流引擎
└── langgraph_service.py   # 服务接口层
```

## 工作流类型

### 1. 代码解释工作流 (Explain)

**流程**: 代码分析 → 代码解释 → 最终化处理

**代理**:
- `CodeAnalyzerAgent`: 进行代码质量分析
- `CodeExplainerAgent`: 生成详细的代码解释

**特性**:
- 自动代码质量评分
- 结构化分析结果
- 优化建议生成

### 2. 问题求解工作流 (Answer)

**流程**: 问题分析 → 方案生成 → 方案验证 → 最终化处理

**代理**:
- `ProblemSolverAgent`: 生成多种难度的解决方案

**特性**:
- 自动问题分类
- 三种难度的解决方案
- 代码完整性验证

### 3. 智能对话工作流 (Talk)

**流程**: 对话处理 → 上下文增强 → 最终化处理

**代理**:
- `ConversationAgent`: 处理智能对话
- 上下文增强节点: 提供额外的上下文信息

**特性**:
- 对话历史管理
- 上下文感知回复
- 动态话题切换

## 状态管理

### WorkflowState结构

```python
class WorkflowState(TypedDict):
    # 基础信息
    session_id: str
    request_id: str
    request_type: str
    
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
    
    # 工作流控制
    processing_steps: List[str]
    errors: List[str]
    warnings: List[str]
    workflow_complete: bool
```

## 监控和管理

### 工作流监控界面

访问路径: `/admin/workflow-monitor/`

**功能**:
- 实时工作流状态监控
- 请求统计和性能分析
- 错误日志和调试信息
- 工作流引擎管理操作

**权限**: 需要管理员权限

### API监控接口

- `GET /admin/workflow-status/`: 获取实时工作流状态
- `POST /admin/clear-cache/`: 清除工作流缓存
- `POST /admin/restart-engine/`: 重启工作流引擎

## 配置和部署

### 1. 依赖安装

```bash
pip install -r requirements.txt
```

新增依赖:
- `langgraph==0.2.50`
- `langchain==0.3.10`
- `langchain-core==0.3.20`
- `langchain-openai==0.2.10`

### 2. 环境配置

在`.env`文件中配置API密钥:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1
```

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

## 开发指南

### 添加新代理

1. 在`langgraph_agents.py`中继承`BaseAgent`类
2. 实现`process`方法
3. 在工作流引擎中注册代理

```python
class CustomAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="custom_agent",
            role="自定义专家",
            system_prompt="你是一个专业的...",
            temperature=0.7
        )
        super().__init__(config)
    
    async def process(self, state: WorkflowState) -> WorkflowState:
        # 实现处理逻辑
        return state
```

### 创建新工作流

1. 在`langgraph_workflow.py`中定义新的工作流
2. 添加节点和边
3. 在服务接口中暴露新功能

```python
# 新工作流定义
new_workflow = StateGraph(WorkflowState)
new_workflow.add_node("step1", self._step1_node)
new_workflow.add_node("step2", self._step2_node)
new_workflow.add_edge(START, "step1")
new_workflow.add_edge("step1", "step2")
new_workflow.add_edge("step2", END)

self.workflows["new_type"] = new_workflow.compile(checkpointer=self.memory)
```

### 扩展状态结构

在`workflow_state.py`中扩展`WorkflowState`:

```python
class WorkflowState(TypedDict):
    # 现有字段...
    
    # 新增字段
    custom_data: Optional[Dict[str, Any]]
    analysis_metrics: Optional[List[Dict]]
```

## 性能优化

### 1. 并行处理

对于独立的代理任务，可以启用并行处理:

```python
config = WorkflowConfig(
    workflow_type="custom",
    enable_parallel_processing=True,
    max_iterations=10
)
```

### 2. 缓存机制

工作流结果会自动缓存在内存中，支持会话级别的状态持久化。

### 3. 超时控制

每个工作流都有超时保护:

```python
workflow_config = WorkflowConfig(
    timeout_seconds=300,  # 5分钟超时
    max_iterations=10
)
```

## 故障排除

### 常见问题

1. **工作流执行失败**
   - 检查API密钥配置
   - 查看错误日志: `logs/django.log`
   - 验证网络连接

2. **内存使用过高**
   - 定期清除工作流缓存
   - 限制对话历史长度
   - 监控活跃会话数量

3. **处理时间过长**
   - 调整代理温度参数
   - 优化提示词长度
   - 启用并行处理

### 调试工具

1. **工作流监控面板**: 实时查看工作流状态
2. **详细日志**: 每个处理步骤都有时间戳记录
3. **状态检查器**: 验证工作流状态的完整性

## 最佳实践

### 1. 提示词管理

- 使用`PromptManager`统一管理提示词
- 为不同代理定制专业化提示词
- 定期优化提示词效果

### 2. 错误处理

- 在每个代理中实现异常捕获
- 提供有意义的错误消息
- 支持优雅降级

### 3. 状态设计

- 保持状态结构的扁平化
- 避免存储大量数据在状态中
- 使用合适的数据类型

### 4. 监控和日志

- 启用详细的执行日志
- 监控关键性能指标
- 设置告警机制

## 版本兼容性

- **LangGraph**: 0.2.50+
- **LangChain**: 0.3.10+
- **Django**: 5.0.14
- **Python**: 3.11+

## 后续规划

1. **更多代理类型**: 添加文档生成、测试自动化等代理
2. **高级工作流**: 支持条件分支、循环控制
3. **分布式处理**: 支持多节点部署
4. **实时协作**: WebSocket支持实时交互
5. **插件系统**: 支持第三方代理插件

---

*此文档随着系统更新而持续维护，请关注最新版本。*