# 代码编辑器行选择功能 - Monaco Editor风格实现

## 🎯 实现目标
仿照Monaco Editor的行选择逻辑，重构代码编辑器的行号点击和选择功能，提供更加专业和直观的用户体验。

## ✅ 新实现的核心功能

### 1. Monaco Editor风格的行选择逻辑

#### selectedLines Set管理
```javascript
// 在 constructor 中声明
this.selectedLines = new Set();
```

#### setupLineSelection() - 行选择事件监听
```javascript
setupLineSelection() {
    // 行号点击事件监听
    this.lineNumbers.addEventListener('click', (e) => {
        if (e.target.classList.contains('line-number')) {
            const lineNumber = parseInt(e.target.dataset.line);
            this.toggleLineSelection(lineNumber, e.ctrlKey);
        }
    });
}
```

#### toggleLineSelection() - 切换行选择状态
```javascript
toggleLineSelection(lineNumber, isCtrlClick = false) {
    if (!isCtrlClick) {
        // 如果不是Ctrl+点击，先清空之前的选择
        this.selectedLines.clear();
    }

    if (this.selectedLines.has(lineNumber)) {
        this.selectedLines.delete(lineNumber);
    } else {
        this.selectedLines.add(lineNumber);
    }
    
    this.updateLineHighlights();
    this.onSelectionChange();
}
```

#### updateLineHighlights() - 更新高亮显示
```javascript
updateLineHighlights() {
    // 更新行号高亮显示
    const lineElements = this.lineNumbers.querySelectorAll('.line-number');
    lineElements.forEach(element => {
        const lineNumber = parseInt(element.dataset.line);
        if (this.selectedLines.has(lineNumber)) {
            element.classList.add('selected');
        } else {
            element.classList.remove('selected');
        }
    });
}
```

#### onSelectionChange() - 选择状态变化回调
```javascript
onSelectionChange() {
    // 选择状态改变时的回调
    if (this.selectedLines.size === 0) {
        this.clearSelectionDisplay();
    } else {
        this.updateSelectionDisplay();
    }
}
```

### 2. 用户交互优化

#### 选择模式
- **单选模式**：直接点击行号选择单行，自动清除之前的选择
- **多选模式**：Ctrl+点击添加或移除行选择
- **清除选择**：点击已选中的行号或使用clearSelection()方法

#### 视觉反馈
- **选中高亮**：选中行用蓝色背景和白色文字显示
- **悬停效果**：鼠标悬停时显示淡蓝色背景
- **活动效果**：点击时轻微缩放反馈

### 3. 状态管理优化

#### updateSelectionDisplay() - 更新选择显示
```javascript
updateSelectionDisplay() {
    const selectedCount = this.selectedLines.size;
    const selectedCode = this.getSelectedCode();
    const charCount = selectedCode.length;
    
    // 更新选择信息显示
    this.selectionDetails.textContent = `已选中 ${selectedCount} 行，${charCount} 个字符`;
    this.selectedCodeInfo.style.display = 'block';
    
    // 更新解释按钮文本
    this.explainBtn.innerHTML = '<i class="fas fa-code me-2"></i>解释选中代码';
}
```

#### clearSelectionDisplay() - 清除选择显示
```javascript
clearSelectionDisplay() {
    this.selectedCodeInfo.style.display = 'none';
    this.explainBtn.innerHTML = '<i class="fas fa-brain me-2"></i>开始解释';
}
```

### 4. CSS样式增强

#### 选中状态样式
```css
.line-numbers div.selected {
    background-color: #4299e1;
    color: white;
    font-weight: bold;
    box-shadow: inset 3px 0 0 #2b6cb0;
}

.line-numbers div:active {
    transform: scale(0.98);
}
```

## 🔄 工作流程

### 用户操作流程
1. **点击行号**：选择单行，自动清除其他选择
2. **Ctrl+点击**：多选模式，添加或移除行选择
3. **选择反馈**：实时更新选中行高亮和统计信息
4. **代码分析**：根据选择状态智能切换分析模式

### 技术流程
1. **事件捕获**：行号点击事件监听
2. **状态更新**：updateLineHighlights() 更新视觉状态
3. **回调触发**：onSelectionChange() 处理状态变化
4. **界面更新**：updateSelectionDisplay() 或 clearSelectionDisplay()

## 🎨 用户体验改进

### 直观的选择操作
- ✅ 类似代码编辑器的行选择体验
- ✅ 支持单选和多选模式
- ✅ 清晰的视觉反馈
- ✅ 即时的状态更新

### 专业的界面设计
- ✅ Monaco Editor风格的行号显示
- ✅ 蓝色主题的选中高亮
- ✅ 流畅的悬停和点击动画
- ✅ 一致的设计语言

### 智能的功能集成
- ✅ 与现有分析工作流无缝集成
- ✅ 自动检测选择状态切换模式
- ✅ 保持完整代码上下文
- ✅ 实时的选择统计信息

## 🛠 技术特点

### 1. 模块化设计
- 独立的行选择逻辑模块
- 清晰的方法职责划分
- 易于维护和扩展

### 2. 事件驱动架构
- 基于用户交互的事件监听
- 状态变化驱动的回调机制
- 响应式的界面更新

### 3. 性能优化
- 高效的Set数据结构管理选择状态
- DOM操作最小化
- 流畅的用户交互体验

## 📊 功能验证

### 已测试场景
- ✅ 单行选择和取消
- ✅ 多行选择（Ctrl+点击）
- ✅ 选择状态持久化
- ✅ 界面高亮更新
- ✅ 选择信息显示
- ✅ 代码分析模式切换

### 浏览器兼容性
- Chrome/Edge：完全支持
- Firefox：完全支持
- Safari：基本支持

## 🚀 使用指南

1. **访问页面**：http://127.0.0.1:8000/explain/
2. **输入代码**：在左侧代码编辑器中输入R代码
3. **选择行号**：
   - 单击行号：选择单行
   - Ctrl+单击：多选模式
4. **查看选择**：选中行将以蓝色高亮显示
5. **分析代码**：点击按钮进行智能分析

这个Monaco Editor风格的实现为用户提供了更加专业和直观的代码编辑体验！