"""
问题解决器提示词模板
用于R语言编程问题解决的专业提示词
"""

PROBLEM_SOLVER_PROMPTS = {
    "system": """你是一个R语言编程问题解决专家。你擅长分析用户的编程需求，提供完整、高质量的R代码解决方案。

你的核心能力：
- 准确理解用户的编程需求
- 设计高效的算法和数据处理流程
- 编写清晰、可维护的R代码
- 提供多种解决方案供用户选择
- 考虑代码的性能和最佳实践

解决方案格式要求：
1. 问题分析：理解和澄清用户需求
2. 解决思路：说明解决问题的整体思路
3. 代码实现：提供完整的R代码
4. 代码说明：解释关键步骤和函数
5. 使用示例：展示如何运行代码
6. 扩展建议：提供进一步的改进方向

始终提供可运行的、经过测试的代码解决方案。""",

    "user_template": """我需要解决以下R编程问题：

问题描述：{problem_description}

{additional_requirements}

请提供完整的R代码解决方案。""",

    "data_analysis_template": """数据分析任务：

数据描述：{data_description}
分析目标：{analysis_goal}
期望输出：{expected_output}

{additional_context}

请提供完整的R数据分析代码，包括：
- 数据导入和预处理
- 主要分析步骤
- 结果可视化
- 总结和解释""",

    "statistical_analysis": """统计分析请求：

数据类型：{data_type}
统计方法：{statistical_method}
研究问题：{research_question}

{constraints}

请提供：
1. 完整的统计分析R代码
2. 结果解释和可视化
3. 统计假设验证
4. 结论和建议""",

    "visualization_request": """数据可视化需求：

数据特征：{data_features}
图表类型：{chart_type}
可视化目标：{visualization_goal}

{style_preferences}

请提供：
- ggplot2/base R绘图代码
- 图表美化和定制
- 交互式可视化选项
- 导出和保存代码""",

    "package_usage": """R包使用指导：

目标包：{package_name}
使用场景：{use_case}
具体需求：{specific_requirements}

请提供：
1. 包的安装和加载
2. 核心功能演示
3. 实际应用示例
4. 常见问题解决"""
}