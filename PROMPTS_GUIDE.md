# 📝 模块化提示词系统使用指南

## 🎯 概述

新的模块化提示词系统将所有AI提示词分类存储在独立文件中，便于管理、调整和维护。

## 📁 文件结构

```
r_assistant/
├── prompts/                          # 提示词模块
│   ├── __init__.py                   # 模块初始化
│   ├── code_explainer_prompts.py     # 代码解释提示词
│   ├── problem_solver_prompts.py     # 问题解决提示词
│   ├── conversation_prompts.py       # 对话交互提示词
│   ├── code_analyzer_prompts.py      # 代码分析提示词
│   └── system_prompts.py             # 系统级提示词
└── services/
    ├── advanced_prompt_manager.py    # 高级提示词管理器
    └── prompt_manager.py             # 兼容性接口
```

## 🚀 快速开始

### 基本使用

```python
from services.advanced_prompt_manager import advanced_prompt_manager

# 获取代码解释提示词
prompt = advanced_prompt_manager.get_prompt(
    'code_explainer', 'user_template',
    code="x <- 1:10\nprint(x)",
    additional_context="这是一个简单示例"
)

# 获取问题解决提示词
prompt = advanced_prompt_manager.get_prompt(
    'problem_solver', 'user_template',
    problem_description="如何创建散点图",
    additional_requirements="使用ggplot2包"
)
```

### 兼容性接口

```python
from services.prompt_manager import PromptManager

# 旧接口仍然可用
explain_prompt = PromptManager.get_explain_prompt("code here")
answer_prompt = PromptManager.get_answer_prompt("problem here")
chat_prompt = PromptManager.get_talk_prompt("message", "context")
```

## 📋 提示词类别

### 1. 代码解释器 (`code_explainer`)

**可用提示词:**
- `system` - 系统角色定义
- `user_template` - 用户代码解释请求
- `analysis_template` - 深度代码分析
- `error_explanation` - 错误解释
- `optimization_advice` - 优化建议

**示例:**
```python
# 基本代码解释
prompt = advanced_prompt_manager.get_prompt(
    'code_explainer', 'user_template',
    code="data <- read.csv('file.csv')",
    additional_context="数据导入操作"
)

# 错误解释
prompt = advanced_prompt_manager.get_prompt(
    'code_explainer', 'error_explanation',
    code="problematic_code_here",
    error_msg="Error: object not found"
)
```

### 2. 问题解决器 (`problem_solver`)

**可用提示词:**
- `system` - 系统角色定义
- `user_template` - 基本问题求解
- `data_analysis_template` - 数据分析任务
- `statistical_analysis` - 统计分析
- `visualization_request` - 数据可视化
- `package_usage` - R包使用指导

**示例:**
```python
# 数据分析任务
prompt = advanced_prompt_manager.get_prompt(
    'problem_solver', 'data_analysis_template',
    data_description="销售数据CSV文件",
    analysis_goal="分析销售趋势",
    expected_output="趋势图表和总结报告"
)

# 可视化请求
prompt = advanced_prompt_manager.get_prompt(
    'problem_solver', 'visualization_request',
    data_features="数值型变量x和y",
    chart_type="散点图",
    visualization_goal="展示变量间相关性"
)
```

### 3. 对话代理 (`conversation`)

**可用提示词:**
- `system` - 系统角色定义
- `greeting` - 欢迎消息
- `user_template` - 用户对话
- `learning_guidance` - 学习指导
- `casual_chat` - 轻松对话
- `encouragement` - 鼓励支持
- `community_help` - 社区指导
- `career_advice` - 职业建议

### 4. 代码分析器 (`code_analyzer`)

**可用提示词:**
- `system` - 系统角色定义
- `quality_analysis` - 质量分析
- `performance_analysis` - 性能分析
- `style_check` - 风格检查
- `security_analysis` - 安全分析
- `refactoring_suggestions` - 重构建议
- `best_practices` - 最佳实践
- `complexity_analysis` - 复杂度分析

### 5. 系统级提示词 (`system`)

**可用提示词:**
- `base_system` - 基础系统提示
- `error_handling` - 错误处理指导
- `code_quality` - 代码质量标准
- `learning_support` - 学习支持方针
- `context_awareness` - 上下文感知
- `safety_guidelines` - 安全指导
- `continuous_improvement` - 持续改进

## 🔧 高级功能

### 提示词管理

```python
# 列出所有可用提示词
available = advanced_prompt_manager.list_available_prompts()
print(available)

# 验证所有提示词
validation = advanced_prompt_manager.validate_prompts()
print(f"有效: {len(validation['valid'])}")
print(f"无效: {len(validation['invalid'])}")

# 获取提示词详细信息
info = advanced_prompt_manager.get_prompt_info('code_explainer', 'system')
print(f"长度: {info['length']} 字符")
print(f"模板变量: {info['template_variables']}")
```

### 兼容性方法

```python
# 使用兼容性接口的新功能
data_prompt = PromptManager.get_data_analysis_prompt(
    "用户行为数据", "用户画像分析", "分类报告"
)

viz_prompt = PromptManager.get_visualization_prompt(
    "时间序列数据", "折线图", "趋势分析"
)

analysis_prompt = PromptManager.get_analysis_prompt(
    "code_to_analyze", "performance"  # quality, performance, style, security
)
```

## ✏️ 自定义提示词

### 修改现有提示词

直接编辑对应的提示词文件：

```python
# 编辑 prompts/code_explainer_prompts.py
CODE_EXPLAINER_PROMPTS = {
    "system": """你的自定义系统提示词...""",
    "user_template": """你的自定义用户模板...
    
代码: {code}
上下文: {additional_context}
    """,
    # ... 其他提示词
}
```

### 添加新提示词类型

在相应文件中添加新的提示词：

```python
# 在 prompts/code_explainer_prompts.py 中添加
CODE_EXPLAINER_PROMPTS = {
    # ... 现有提示词
    "my_custom_prompt": """我的自定义提示词模板
    
    参数1: {param1}
    参数2: {param2}
    """,
}
```

然后使用：

```python
prompt = advanced_prompt_manager.get_prompt(
    'code_explainer', 'my_custom_prompt',
    param1="值1", param2="值2"
)
```

## 🔄 与LangGraph集成

提示词系统已与LangGraph代理完全集成：

```python
# 在 langgraph_agents.py 中
from .advanced_prompt_manager import advanced_prompt_manager

class CodeExplainerAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            system_prompt=advanced_prompt_manager.get_prompt('code_explainer', 'system')
        )
```

## 🧪 测试和验证

运行提示词系统测试：

```bash
cd r_assistant
python -c "from services.advanced_prompt_manager import advanced_prompt_manager; print('✅ 系统正常')"
```

## 📝 最佳实践

1. **模板变量**: 使用 `{variable_name}` 格式
2. **命名规范**: 使用描述性的提示词名称
3. **分类管理**: 将相关提示词放在同一文件中
4. **文档注释**: 为每个提示词添加说明注释
5. **测试验证**: 修改后运行验证测试

## 🚨 注意事项

- 修改提示词文件后需要重启Django服务器
- 使用模板变量时确保提供所有必需参数
- 新增提示词类别需要同时更新 `__init__.py`
- 保持向后兼容性，不要删除现有的提示词接口

## 📞 支持

如需添加新的提示词类型或修改现有提示词，请参考现有文件的格式，或联系开发团队。