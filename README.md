# R 语言智能助手

这是一个基于 Django 和 **LangGraph 工作流框架** 的 Web 应用，面向 R 语言学习者与开发者，提供智能化代码解释、作业求解与对话式 AI 助手功能。

## ✨ 主要功能

### 🎯 三大核心功能

1. **Answer (代码生成)** 📝
   - 输入R语言作业题目
   - AI生成三种不同难度的解决方案
   - 每个方案包含详细的中文注释
   - 自动命名程序文件和包依赖分析

2. **Explain (代码解释)** 💡
   - 粘贴您的R语言代码
   - AI用平易近人的语气解释代码功能
   - 逐步分析代码逻辑和意义
   - 自动代码质量评分和优化建议

3. **Talk (智能对话)** 💬
   - 与R语言专家进行友好交流
   - 获取学习建议和编程技巧
   - 讨论R语言相关问题
   - 上下文感知的专业指导

### 🚀 新增: LangGraph工作流系统

本项目现已集成 **LangGraph 工作流框架**，提供：

- **状态化工作流**: 复杂任务的步骤化处理和状态管理
- **多代理协作**: 专业化AI代理协同工作
- **完整可观测性**: 详细的执行跟踪和性能监控
- **高级错误处理**: 更强的容错和重试机制
- **工作流监控**: 实时监控面板 (`/admin/workflow-monitor/`)

## 🛠️ 快速开始

### 环境要求
- Python 3.11+
- Django 5.0.14
- LangGraph 0.2.50+
- DeepSeek API Key

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/TTAWDTT/YJYsaver-R-assistant.git
cd YJYsaver-R-assistant
```

2. 安装依赖 (包含LangGraph)
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件并填入以下配置：
```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1
SECRET_KEY=your_django_secret_key
DEBUG=True
```

4. 数据库迁移
```bash
cd r_assistant
python manage.py makemigrations
python manage.py migrate
```

5. 创建超级用户（可选）
```bash
python manage.py createsuperuser
```

6. 启动服务
```bash
python manage.py runserver
```

访问 `http://127.0.0.1:8000` 即可使用！

## 🎨 界面特色

### 现代化设计
- ✨ **磨砂玻璃效果** - 高级视觉体验
- 🌟 **动态粒子背景** - 炫酷交互效果
- 🎭 **渐变色主题** - 优雅配色方案
- 📱 **响应式布局** - 完美适配各种设备

### 交互体验
- 🎯 **悬浮动画** - 流畅的卡片交互
- 💫 **图标发光** - 精美的视觉反馈
- 🌈 **脉冲效果** - 吸引用户注意
- ⚡ **平滑过渡** - 自然的动画效果

## 🛠️ 技术架构

### 后端技术
- **Django 5.0.14** - 强大的Web框架
- **LangGraph 0.2.50** - 智能工作流引擎
- **LangChain 0.3.10** - AI应用开发框架
- **DeepSeek Chat API** - 先进的AI语言模型
- **SQLite** - 轻量级数据库
- **模块化设计** - 易于维护和扩展

### 前端技术
- **Bootstrap 5** - 现代化UI框架
- **Font Awesome** - 丰富的图标库
- **Prism.js** - 代码语法高亮
- **CSS3动画** - 高级视觉效果

### LangGraph工作流架构
- **状态图工作流** - 基于有向图的任务流控制
- **多代理系统** - 专业化AI代理协作
- **状态持久化** - 会话级别的状态管理
- **实时监控** - 工作流执行监控和性能分析
- **错误恢复** - 智能错误处理和重试机制

### 代码特色
- 📦 **PromptManager** - 集中化提示词管理
- 🔧 **模块化架构** - 清晰的代码结构
- 🎯 **服务层抽象** - 易于测试和维护
- 📊 **完整日志记录** - 便于调试和分析
- 🔄 **工作流引擎** - LangGraph驱动的智能处理

## 📁 项目结构

```
r_assistant/
├── core/                   # 核心应用
│   ├── models.py          # 数据模型
│   ├── views.py           # 视图逻辑
│   ├── urls.py            # URL配置
│   └── templates/         # 模板文件
├── services/              # 服务层
│   ├── ai_service.py      # AI服务接口
│   ├── prompt_manager.py  # 提示词管理
│   └── code_analyzer.py   # 代码分析器
├── static/                # 静态文件
│   ├── css/              # 样式文件
│   ├── js/               # JavaScript文件
│   └── img/              # 图片资源
└── r_assistant/          # 项目配置
    ├── settings.py       # Django设置
    ├── urls.py          # 主URL配置
    └── wsgi.py          # WSGI配置
```

## 🚀 开发指南

### 添加新功能
1. 在 `core/models.py` 中定义数据模型
2. 在 `services/` 中实现业务逻辑
3. 在 `core/views.py` 中创建视图
4. 在 `core/templates/` 中创建模板
5. 在 `static/` 中添加样式和脚本

### API 端点
- `/api/explain/` - 代码解释
- `/api/answer/` - 作业求解
- `/api/talk/` - 智能对话

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

- GitHub: [@TTAWDTT](https://github.com/TTAWDTT)
- 项目地址: [YJYsaver-R-assistant](https://github.com/TTAWDTT/YJYsaver-R-assistant)
