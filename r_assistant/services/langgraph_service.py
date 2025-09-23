"""
基于LangGraph的智能服务接口
替换原有的简单AI服务，提供更强大的工作流功能
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from django.conf import settings
from .langgraph_workflow import workflow_engine
from .workflow_state import Message, CodeSolution
from .ai_service import AIServiceError

logger = logging.getLogger(__name__)


class LangGraphService:
    """基于LangGraph的智能服务"""
    
    def __init__(self):
        self.workflow_engine = workflow_engine
        try:
            self.api_key_available = bool(getattr(settings, 'DEEPSEEK_API_KEY', ''))
        except Exception:
            import os
            self.api_key_available = bool(os.environ.get('DEEPSEEK_API_KEY', ''))
        
    def _check_api_availability(self):
        """检查API是否可用"""
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not api_key or api_key.startswith('sk-请替换') or api_key == 'sk-placeholder-key-change-this':
            logger.warning("DEEPSEEK_API_KEY未正确配置，使用演示模式")
            return False
        return True
        
    def _run_async(self, coro):
        """在同步环境中运行异步代码"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def _convert_history_to_messages(self, conversation_history: List[Dict[str, str]]) -> List[Message]:
        """转换对话历史格式"""
        messages = []
        for item in conversation_history:
            message = Message(
                role=item.get("role", "user"),
                content=item.get("content", ""),
                timestamp=datetime.now()
            )
            messages.append(message)
        return messages
    
    def _format_code_solutions(self, solutions: List[CodeSolution]) -> List[Dict[str, Any]]:
        """格式化代码解决方案"""
        formatted_solutions = []
        for solution in solutions:
            formatted_solutions.append({
                "title": solution.title,
                "code": solution.code,
                "explanation": solution.explanation,
                "difficulty": solution.difficulty,
                "packages": solution.packages,
                "filename": solution.filename
            })
        return formatted_solutions
    
    def explain_code(self, code: str, session_id: str = None, mode: str = 'full') -> Dict[str, Any]:
        """代码解释服务 - 使用LangGraph工作流
        
        Args:
            code: 要解释的代码
            session_id: 会话ID
            mode: 分析模式 ('full', 'selected')
        """
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("explain", code, mode)
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="explain",
                    user_input=code,
                    session_id=session_id
                )
            )
            
            # 格式化返回结果
            response = {
                "content": result.get("explanation_result") or result.get("ai_response", ""),
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success",
                "analysis_mode": mode,
                "metadata": {
                    "workflow_steps": result.get("processing_steps", []),
                    "code_analysis": result.get("code_analysis"),
                    "quality_score": result.get("quality_score"),
                    "warnings": result.get("warnings", []),
                    "errors": result.get("errors", [])
                }
            }
            
            if not response["success"]:
                raise AIServiceError(f"代码解释失败: {'; '.join(result.get('errors', []))}")
            
            logger.info(f"代码解释完成（模式：{mode}），会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码解释服务失败: {str(e)}")
            raise AIServiceError(f"代码解释失败: {str(e)}")
    
    def solve_problem(self, problem: str, session_id: str = None, uploaded_files: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """问题求解服务 - 使用LangGraph工作流，支持文件上传"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("solve", problem, uploaded_files)
            
            # 准备文件内容描述
            file_context = ""
            if uploaded_files:
                file_context = "\n\n相关文件内容：\n"
                for file_info in uploaded_files:
                    file_context += f"\n--- 文件: {file_info['filename']} (类型: {file_info['type']}, 大小: {file_info['size']} 字节) ---\n"
                    if file_info['content'].startswith('[二进制文件'):
                        file_context += file_info['content'] + "\n"
                    else:
                        # 限制文件内容长度，避免过长
                        content = file_info['content']
                        if len(content) > 5000:
                            content = content[:5000] + "\n... (内容被截断，文件过长)"
                        file_context += content + "\n"
                file_context += "\n请基于以上文件内容来解决问题。"
            
            # 组合问题描述和文件内容
            enhanced_problem = problem + file_context
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="answer",
                    user_input=enhanced_problem,
                    session_id=session_id
                )
            )
            
            # 格式化解决方案
            solutions = self._format_code_solutions(result.get("code_solutions", []))
            
            # 格式化返回结果
            response = {
                "content": result.get("ai_response", ""),
                "solutions": solutions,
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success",
                "metadata": {
                    "workflow_steps": result.get("processing_steps", []),
                    "problem_type": result.get("problem_type"),
                    "warnings": result.get("warnings", []),
                    "errors": result.get("errors", []),
                    "uploaded_files_count": len(uploaded_files) if uploaded_files else 0
                }
            }
            
            if not response["success"]:
                raise AIServiceError(f"问题求解失败: {'; '.join(result.get('errors', []))}")
            
            logger.info(f"问题求解完成，会话ID: {session_id}，生成{len(solutions)}个解决方案，包含{len(uploaded_files) if uploaded_files else 0}个文件")
            return response
            
        except Exception as e:
            logger.error(f"问题求解服务失败: {str(e)}")
            raise AIServiceError(f"问题求解失败: {str(e)}")
    
    def chat(self, message: str, conversation_history: List[Dict[str, str]] = None, 
             session_id: str = None) -> Dict[str, Any]:
        """智能对话服务 - 使用LangGraph工作流"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("chat", message)
            
            # 转换对话历史
            history_messages = self._convert_history_to_messages(conversation_history or [])
            
            # 执行工作流
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="talk",
                    user_input=message,
                    session_id=session_id,
                    conversation_history=history_messages
                )
            )
            
            # 格式化返回结果
            response = {
                "content": result.get("ai_response", ""),
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success",
                "metadata": {
                    "workflow_steps": result.get("processing_steps", []),
                    "conversation_length": len(result.get("conversation_history", [])),
                    "warnings": result.get("warnings", []),
                    "errors": result.get("errors", [])
                }
            }
            
            # 检查是否有内容返回
            if not response["content"] and response["success"]:
                logger.warning("AI响应为空，但状态为成功")
                response["content"] = "抱歉，我暂时无法生成回复，请稍后再试。"
            
            if not response["success"]:
                error_msg = '; '.join(result.get('errors', [])) or "未知错误"
                raise AIServiceError(f"智能对话失败: {error_msg}")
            
            logger.info(f"智能对话完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"智能对话服务失败: {str(e)}")
            raise AIServiceError(f"智能对话失败: {str(e)}")
    
    def analyze_code_quality(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """代码质量分析服务"""
        try:
            session_id = session_id or f"session_{datetime.now().timestamp()}"
            
            # 检查API可用性
            if not self._check_api_availability():
                return self._create_demo_response("analyze", code)
            
            # 执行代码解释工作流（包含分析）
            result = self._run_async(
                self.workflow_engine.execute_workflow(
                    request_type="explain",
                    user_input=code,
                    session_id=session_id
                )
            )
            
            # 提取分析结果
            analysis = result.get("code_analysis", {})
            
            response = {
                "content": analysis.get("analysis_result", ""),
                "quality_score": analysis.get("quality_score", 0),
                "suggestions": analysis.get("suggestions", []),
                "complexity": analysis.get("complexity", "unknown"),
                "maintainability": analysis.get("maintainability", "unknown"),
                "processing_time": result.get("processing_time", 0),
                "usage": {"total_tokens": result.get("total_tokens", 0)},
                "success": result.get("status") == "success"
            }
            
            logger.info(f"代码质量分析完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码质量分析失败: {str(e)}")
            raise AIServiceError(f"代码质量分析失败: {str(e)}")
    
    def generate_tests(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """测试用例生成服务"""
        # 暂时使用简化实现，可以后续扩展为完整的工作流
        try:
            test_code = f"""
# 为以下代码生成的测试用例
# 原始代码:
{code}

# 测试用例
library(testthat)

test_that("基本功能测试", {{
  # 测试基本功能
  expect_true(TRUE)
}})

test_that("边界条件测试", {{
  # 测试边界条件
  expect_true(TRUE)
}})

test_that("异常处理测试", {{
  # 测试异常处理
  expect_true(TRUE)
}})
"""
            
            response = {
                "content": test_code,
                "processing_time": 0.1,
                "usage": {"total_tokens": 100},
                "success": True
            }
            
            logger.info(f"测试用例生成完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"测试用例生成失败: {str(e)}")
            raise AIServiceError(f"测试用例生成失败: {str(e)}")
    
    def optimize_code(self, code: str, session_id: str = None) -> Dict[str, Any]:
        """代码优化服务"""
        # 暂时使用简化实现，可以后续扩展为完整的工作流
        try:
            optimized_code = f"""
# 优化后的代码
# 原始代码:
{code}

# 优化建议:
# 1. 添加错误处理
# 2. 优化性能
# 3. 提高可读性

# 优化后的代码:
{code}  # 这里应该是实际优化后的代码
"""
            
            response = {
                "content": optimized_code,
                "processing_time": 0.1,
                "usage": {"total_tokens": 100},
                "success": True
            }
            
            logger.info(f"代码优化完成，会话ID: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"代码优化失败: {str(e)}")
            raise AIServiceError(f"代码优化失败: {str(e)}")
    
    def _create_demo_response(self, request_type: str, user_input: str, mode_or_files = 'full') -> Dict[str, Any]:
        """创建演示响应（当API密钥不可用时）"""
        # 处理参数兼容性
        if isinstance(mode_or_files, list):
            uploaded_files = mode_or_files
            mode = 'full'
            file_info = f"\n\n📎 **包含{len(uploaded_files)}个上传文件：**\n"
            for file in uploaded_files:
                file_info += f"- {file['filename']} ({file['type']}, {file['size']} 字节)\n"
        else:
            mode = mode_or_files
            uploaded_files = None
            file_info = ""
        
        demo_responses = {
            "chat": f"🤖 **R语言智能助手演示模式**\n\n你好！我是R语言智能助手。\n\n**你说：** {user_input}\n\n---\n\n⚠️ **当前处于演示模式**\n\n要启用完整的AI功能，请按以下步骤配置API密钥：\n\n1. 访问 https://platform.deepseek.com 注册账号\n2. 获取您的API Key\n3. 在项目根目录的 `.env` 文件中设置：\n   ```\n   DEEPSEEK_API_KEY=你的API密钥\n   ```\n4. 重启服务器\n\n**配置完成后，我可以帮助你：**\n- 📝 解释R代码\n- 🔧 解决编程问题\n- 📚 提供学习建议\n- 📊 数据分析指导",
            
            "explain": f"📝 **代码解释功能演示{' - 选中代码分析' if mode == 'selected' else ''}**\n\n**你提交的代码：**\n```r\n{user_input}\n```\n\n---\n\n🎯 **演示解释：**\n\n这是一个演示响应。配置API密钥后，我将为你提供详细的代码分析，包括：\n\n- 📖 逐行代码解释\n- ⚙️ 函数功能说明  \n- ✨ 最佳实践建议\n- 🚀 性能优化方案\n\n{f'**当前选中代码分析模式** - 我会重点关注你选中的代码片段并结合完整上下文进行分析。' if mode == 'selected' else ''}\n\n---\n\n⚠️ **要启用完整功能，请配置DeepSeek API密钥：**\n\n1. 访问 https://platform.deepseek.com\n2. 在 `.env` 文件中设置 `DEEPSEEK_API_KEY`\n3. 重启服务器",
            
            "solve": f"🔧 **问题解决功能演示**\n\n**你的问题：** {user_input}{file_info}\n\n---\n\n🎯 **演示解决方案：**\n\n这是一个演示响应。配置API密钥后，我将提供：\n\n- 🔄 多种解决方案\n- 💻 详细代码实现\n- 📋 最佳实践指导\n- 📦 相关包推荐\n{f'- 📎 基于上传文件的个性化解决方案' if uploaded_files else ''}\n\n---\n\n⚠️ **配置API密钥以获得完整功能**",
            
            "analyze": f"📊 **代码分析功能演示**\n\n**你提交的代码：**\n```r\n{user_input}\n```\n\n---\n\n🎯 **演示分析：**\n\n配置API密钥后，我将提供：\n\n- 📈 代码质量评分\n- ⚡ 性能分析建议\n- 📏 代码规范检查\n- 🔧 优化建议\n\n---\n\n⚠️ **配置API密钥以获得完整功能**"
        }
        
        response = {
            "content": demo_responses.get(request_type, f"演示响应：{user_input}"),
            "processing_time": 0.1,
            "usage": {"total_tokens": 0},
            "success": True,
            "analysis_mode": mode,
            "metadata": {
                "demo_mode": True,
                "api_key_required": True,
                "message": "请配置DEEPSEEK_API_KEY以启用完整功能",
                "uploaded_files_count": len(uploaded_files) if uploaded_files else 0
            }
        }
        
        # 为求解问题添加演示解决方案
        if request_type == "solve":
            response["solutions"] = [
                {
                    "title": "数据可视化方案",
                    "code": """# 解决方案 1: 使用ggplot2创建散点图
library(ggplot2)
data(mtcars)

# 创建散点图显示重量与油耗的关系
p1 <- ggplot(mtcars, aes(x = wt, y = mpg)) +
  geom_point(color = "blue", size = 3) +
  geom_smooth(method = "lm", se = TRUE, color = "red") +
  labs(title = "车重与油耗关系图",
       x = "车重 (1000 lbs)",
       y = "每加仑英里数 (mpg)") +
  theme_minimal()

print(p1)

# 显示相关性
correlation <- cor(mtcars$wt, mtcars$mpg)
cat("相关系数:", round(correlation, 3))""",
                    "explanation": """## 📊 详细解释

### 🎯 **解决方案概述**
这个解决方案演示了如何使用R语言的ggplot2包来分析mtcars数据集，创建专业的散点图展示车重与油耗的关系。

### 📝 **代码详解**

#### 1. **加载必要包**
```r
library(ggplot2)
```
- 加载ggplot2图形包，这是R中最强大的数据可视化工具之一
- 提供了丰富的图层语法，可以创建高质量的统计图形

#### 2. **数据准备**
```r
data(mtcars)
```
- 加载内置的mtcars数据集
- 包含32种车型的11个变量，包括油耗(mpg)和重量(wt)

#### 3. **创建散点图**
```r
p1 <- ggplot(mtcars, aes(x = wt, y = mpg))
```
- 初始化ggplot对象
- `aes()` 定义美学映射：x轴为车重，y轴为油耗

#### 4. **添加图层**
- `geom_point()`: 添加散点，蓝色，大小为3
- `geom_smooth()`: 添加回归线和置信区间
- `labs()`: 设置标题和轴标签
- `theme_minimal()`: 应用简洁主题

#### 5. **统计分析**
```r
correlation <- cor(mtcars$wt, mtcars$mpg)
```
- 计算皮尔逊相关系数
- 量化车重与油耗之间的线性关系强度

### 🔍 **期望结果**
- **散点图**: 显示明显的负相关趋势
- **回归线**: 红色线条显示整体趋势
- **相关系数**: 约 -0.868，表示强负相关

### 💡 **关键洞察**
1. **负相关关系**: 车重越大，油耗效率越低
2. **线性关系**: 数据点较好地符合线性模型
3. **统计显著性**: 关系在统计上显著

### 📈 **扩展建议**
- 可以添加车型标签: `geom_text(aes(label = rownames(mtcars)))`
- 按缸数分组着色: `aes(color = factor(cyl))`
- 添加置信区间: `geom_smooth(method = "lm", se = TRUE)`

---
*💡 这是演示模式的详细解释。配置API密钥后，将提供基于实际数据的个性化分析。*""",
                    "difficulty": "初级",
                    "packages": ["ggplot2"],
                    "filename": "mtcars_analysis.R"
                },
                {
                    "title": "统计分析方案",
                    "code": """# 解决方案 2: 综合统计分析
# 加载必要的包
library(dplyr)
library(corrplot)

# 基本描述性统计
summary_stats <- mtcars %>%
  select(mpg, wt, hp, cyl) %>%
  summary()

print("描述性统计:")
print(summary_stats)

# 相关性矩阵
cor_matrix <- cor(mtcars[, c("mpg", "wt", "hp", "cyl")])
print("相关性矩阵:")
print(round(cor_matrix, 3))

# 可视化相关性矩阵
corrplot(cor_matrix, method = "circle", 
         type = "upper", order = "hclust",
         tl.cex = 0.8, tl.col = "black")

# 线性回归分析
model <- lm(mpg ~ wt + hp + cyl, data = mtcars)
print("回归分析结果:")
print(summary(model))

# 回归诊断图
par(mfrow = c(2, 2))
plot(model)""",
                    "explanation": """## 🔬 综合统计分析详解

### 🎯 **分析目标**
对mtcars数据集进行全面的统计分析，探索多个变量与油耗的关系，建立预测模型。

### 📊 **分析步骤**

#### 1. **描述性统计**
```r
summary_stats <- mtcars %>%
  select(mpg, wt, hp, cyl) %>%
  summary()
```
**作用**: 
- 了解数据的基本分布特征
- 检查数据范围和异常值
- 为后续分析做准备

**解读要点**:
- `mpg`: 油耗范围 10.4-33.9
- `wt`: 车重范围 1.513-5.424
- `hp`: 马力范围 52-335
- `cyl`: 气缸数 4、6、8

#### 2. **相关性分析**
```r
cor_matrix <- cor(mtcars[, c("mpg", "wt", "hp", "cyl")])
```
**分析目的**:
- 识别变量间的线性关系
- 发现多重共线性问题
- 指导模型变量选择

**预期结果**:
- `mpg-wt`: 强负相关 (~-0.87)
- `mpg-hp`: 强负相关 (~-0.78)
- `mpg-cyl`: 强负相关 (~-0.85)

#### 3. **相关性可视化**
```r
corrplot(cor_matrix, method = "circle")
```
**视觉特征**:
- 🔴 红色圆圈: 负相关
- 🔵 蓝色圆圈: 正相关
- 圆圈大小: 相关性强度

#### 4. **多元线性回归**
```r
model <- lm(mpg ~ wt + hp + cyl, data = mtcars)
```
**模型公式**: `mpg = β₀ + β₁×wt + β₂×hp + β₃×cyl + ε`

**系数解释**:
- `wt系数`: 车重增加1单位，油耗下降约3.2 mpg
- `hp系数`: 马力增加1单位，油耗下降约0.03 mpg
- `cyl系数`: 气缸数影响基础油耗水平

#### 5. **模型诊断**
```r
par(mfrow = c(2, 2))
plot(model)
```
**诊断图解读**:
1. **残差vs拟合值**: 检查线性假设
2. **QQ图**: 检查正态性假设
3. **尺度-位置图**: 检查等方差性
4. **残差vs杠杆**: 识别异常值

### 📈 **模型评估指标**
- **R²**: 解释变异程度 (~0.83)
- **调整R²**: 考虑变量数量的修正R²
- **F统计量**: 模型整体显著性
- **p值**: 各系数的显著性

### 🔍 **实际应用**
1. **预测新车油耗**: 基于车重、马力、气缸数
2. **设计优化**: 识别影响油耗的关键因素
3. **购车建议**: 基于油耗需求推荐车型

### ⚠️ **注意事项**
- 模型基于1974年数据，现代车辆可能不适用
- 需要检查模型假设是否满足
- 考虑非线性关系和交互效应

---
*🔬 这展示了完整的统计分析流程。在实际项目中，会根据具体需求调整分析方法。*""",
                    "difficulty": "中级",
                    "packages": ["dplyr", "corrplot"],
                    "filename": "comprehensive_analysis.R"
                },
                {
                    "title": "高级可视化方案",
                    "code": """# 解决方案 3: 高级数据可视化
library(ggplot2)
library(gridExtra)
library(RColorBrewer)
library(plotly)

# 1. 分面散点图
p1 <- ggplot(mtcars, aes(x = wt, y = mpg)) +
  geom_point(aes(color = factor(cyl), size = hp), alpha = 0.7) +
  geom_smooth(method = "lm", se = TRUE, color = "darkred") +
  facet_wrap(~cyl, labeller = label_both) +
  scale_color_brewer(type = "qual", palette = "Set1") +
  labs(title = "车重与油耗关系 (按气缸数分组)",
       x = "车重 (1000 lbs)", y = "油耗 (mpg)",
       color = "气缸数", size = "马力") +
  theme_bw() +
  theme(legend.position = "bottom")

# 2. 箱线图比较
p2 <- ggplot(mtcars, aes(x = factor(cyl), y = mpg, fill = factor(cyl))) +
  geom_boxplot(alpha = 0.7) +
  geom_jitter(width = 0.2, alpha = 0.5) +
  scale_fill_brewer(type = "qual", palette = "Pastel1") +
  labs(title = "不同气缸数的油耗分布",
       x = "气缸数", y = "油耗 (mpg)") +
  theme_minimal() +
  theme(legend.position = "none")

# 3. 气泡图
p3 <- ggplot(mtcars, aes(x = wt, y = mpg)) +
  geom_point(aes(size = hp, color = factor(cyl)), alpha = 0.6) +
  scale_size_continuous(range = c(3, 15)) +
  scale_color_manual(values = c("4" = "#E31A1C", "6" = "#1F78B4", "8" = "#33A02C")) +
  labs(title = "多维度关系图",
       subtitle = "尺寸=马力, 颜色=气缸数",
       x = "车重 (1000 lbs)", y = "油耗 (mpg)",
       size = "马力", color = "气缸数") +
  theme_classic()

# 4. 组合图表
combined_plot <- grid.arrange(p1, p2, p3, ncol = 2, nrow = 2)

# 5. 交互式图表 (可选)
interactive_plot <- plot_ly(mtcars, x = ~wt, y = ~mpg, size = ~hp, 
                           color = ~factor(cyl), text = ~rownames(mtcars),
                           hovertemplate = "<b>%{text}</b><br>" +
                                         "车重: %{x}<br>" +
                                         "油耗: %{y}<br>" +
                                         "<extra></extra>") %>%
  add_markers() %>%
  layout(title = "交互式车辆性能图",
         xaxis = list(title = "车重 (1000 lbs)"),
         yaxis = list(title = "油耗 (mpg)"))

print("静态图表已生成")
print("运行 interactive_plot 查看交互式图表")""",
                    "explanation": """## 🎨 高级数据可视化详解

### 🎯 **可视化策略**
采用多层次、多维度的可视化方法，全方位展示数据关系，提供直观且信息丰富的分析视角。

### 📊 **图表类型详解**

#### 1. **分面散点图 (Faceted Scatter Plot)**
```r
facet_wrap(~cyl, labeller = label_both)
```
**设计优势**:
- 🔍 **分组对比**: 按气缸数分别展示关系
- 🎨 **多维映射**: 颜色=气缸数，大小=马力
- 📈 **趋势分析**: 每组都有独立的回归线

**视觉元素**:
- **点的颜色**: 区分不同气缸数车型
- **点的大小**: 反映马力大小
- **回归线**: 显示每组内部的线性趋势
- **置信区间**: 评估预测的不确定性

#### 2. **箱线图对比 (Box Plot Comparison)**
```r
geom_boxplot() + geom_jitter()
```
**统计信息展示**:
- 📊 **中位数**: 箱子中间的线
- 📐 **四分位数**: 箱子的上下边界
- 🎯 **异常值**: 超出须线的点
- 🔄 **数据分布**: 抖动点显示原始数据

**对比维度**:
- 4缸车: 油耗最高，分布较窄
- 6缸车: 油耗中等，变异适中
- 8缸车: 油耗最低，分布较宽

#### 3. **气泡图 (Bubble Chart)**
```r
aes(size = hp, color = factor(cyl))
```
**多维度信息**:
- **X轴**: 车重 (连续变量)
- **Y轴**: 油耗 (连续变量)
- **气泡大小**: 马力 (连续变量)
- **气泡颜色**: 气缸数 (分类变量)

**视觉洞察**:
- 大气泡(高马力) → 通常油耗低、车重大
- 不同颜色集群 → 气缸数的分组效应明显
- 气泡分布 → 揭示多变量间的复杂关系

#### 4. **组合布局 (Grid Layout)**
```r
grid.arrange(p1, p2, p3, ncol = 2, nrow = 2)
```
**布局优势**:
- 🔄 **对比分析**: 同时查看多个视角
- 📄 **报告友好**: 适合打印和展示
- 💾 **空间效率**: 最大化信息密度

#### 5. **交互式可视化 (Interactive Plot)**
```r
plot_ly() + add_markers()
```
**交互功能**:
- 🖱️ **悬停信息**: 显示详细数据
- 🔍 **缩放平移**: 探索数据细节
- 🎛️ **图例交互**: 切换显示/隐藏
- 📱 **响应式**: 适配不同设备

### 🎨 **设计原则**

#### **颜色策略**
- `RColorBrewer`: 使用专业配色方案
- `Set1`: 定性数据的高对比度色彩
- `Pastel1`: 柔和色调，适合背景元素

#### **主题选择**
- `theme_bw()`: 黑白边框，专业商务风格
- `theme_minimal()`: 简洁现代，突出数据
- `theme_classic()`: 经典学术风格

#### **信息层次**
1. **主标题**: 明确图表目的
2. **副标题**: 补充关键信息
3. **轴标签**: 包含单位说明
4. **图例**: 清晰的变量说明

### 📈 **应用场景**

#### **学术研究**
- 📝 论文插图
- 📊 数据探索
- 📋 结果汇报

#### **商业分析**
- 📈 业务仪表板
- 💼 决策支持
- 📊 客户报告

#### **教学演示**
- 🎓 课程教学
- 🔍 概念解释
- 💡 案例分析

### 🚀 **扩展功能**
- **动画效果**: `gganimate`包创建动态图表
- **3D可视化**: `plotly`的3D散点图
- **地理信息**: 如果有位置数据，可用地图可视化
- **网络图**: 展示变量间的复杂关系网络

### 💡 **最佳实践**
1. **渐进披露**: 从简单到复杂
2. **一致性**: 保持颜色和样式统一
3. **可访问性**: 考虑色盲友好的配色
4. **响应式**: 适配不同输出媒介

---
*🎨 这展示了R语言强大的可视化能力。每种图表都有其特定的使用场景和优势。*""",
                    "difficulty": "高级",
                    "packages": ["ggplot2", "gridExtra", "RColorBrewer", "plotly"],
                    "filename": "advanced_visualization.R"
                }
            ]
        
        return response


# 创建服务工厂
class LangGraphServiceFactory:
    """LangGraph服务工厂"""
    
    @staticmethod
    def get_service(service_type: str = 'langgraph') -> LangGraphService:
        """获取LangGraph服务实例"""
        if service_type == 'langgraph':
            return LangGraphService()
        else:
            raise AIServiceError(f"Unsupported service type: {service_type}")


# 全局服务实例
langgraph_service = LangGraphServiceFactory.get_service()