/**
 * 流式响应处理器
 * 为代码解释和作业求解提供流式用户体验
 */

class StreamingProcessor {
    constructor() {
        this.isProcessing = false;
        this.currentStream = null;
    }

    /**
     * 创建流式处理器
     * @param {string} endpoint - API端点
     * @param {Object} data - 请求数据
     * @param {Object} callbacks - 回调函数
     */
    async startStream(endpoint, data, callbacks = {}) {
        if (this.isProcessing) {
            throw new Error('已有处理中的请求');
        }

        this.isProcessing = true;
        const {
            onStart = () => {},
            onProgress = () => {},
            onData = () => {},
            onResult = () => {},
            onError = () => {},
            onComplete = () => {}
        } = callbacks;

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // 保留不完整的行

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            await this.handleStreamData(data, {
                                onStart,
                                onProgress,
                                onData,
                                onResult,
                                onError,
                                onComplete
                            });
                        } catch (e) {
                            console.error('解析SSE数据失败:', e);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('流式请求失败:', error);
            onError(error);
        } finally {
            this.isProcessing = false;
            this.currentStream = null;
        }
    }

    /**
     * 处理流式数据
     */
    async handleStreamData(data, callbacks) {
        const { type, data: payload } = data;

        switch (type) {
            case 'start':
                callbacks.onStart(payload);
                break;
            case 'progress':
                callbacks.onProgress(payload);
                break;
            case 'data':
                callbacks.onData(payload);
                break;
            case 'result':
                callbacks.onResult(payload);
                break;
            case 'error':
                callbacks.onError(new Error(payload.message));
                break;
            case 'complete':
                callbacks.onComplete(payload);
                break;
            default:
                console.warn('未知的流式数据类型:', type);
        }
    }

    /**
     * 停止当前流
     */
    stop() {
        this.isProcessing = false;
        if (this.currentStream) {
            this.currentStream.abort();
            this.currentStream = null;
        }
    }
}

/**
 * 流式代码解释器
 */
class StreamingCodeExplainer {
    constructor() {
        this.processor = new StreamingProcessor();
        this.progressContainer = null;
        this.resultContainer = null;
        this.init();
    }

    init() {
        this.createProgressUI();
        this.setupEventListeners();
    }

    createProgressUI() {
        // 创建进度显示组件
        const progressHTML = `
            <div id="streamProgress" class="streaming-progress" style="display: none;">
                <div class="progress-header">
                    <h6 class="text-info mb-2">
                        <i class="fas fa-brain me-2"></i>
                        AI正在分析您的代码
                    </h6>
                </div>
                <div class="progress-content">
                    <div class="progress mb-3" style="height: 8px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                             id="progressBar" style="width: 0%"></div>
                    </div>
                    <div class="progress-message">
                        <span id="progressMessage">准备中...</span>
                        <span class="float-end text-muted">
                            <span id="progressStep">0</span>/<span id="progressTotal">4</span>
                        </span>
                    </div>
                </div>
                <div class="streaming-content mt-3" id="streamingContent">
                    <!-- 流式内容将在这里显示 -->
                </div>
            </div>
        `;

        // 添加到结果容器
        const resultContainer = document.getElementById('resultContainer');
        if (resultContainer) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = progressHTML;
            resultContainer.appendChild(tempDiv.firstElementChild);
        }
    }

    setupEventListeners() {
        const explainBtn = document.getElementById('explainBtn');
        if (explainBtn) {
            explainBtn.addEventListener('click', () => {
                this.startExplanation();
            });
        }
    }

    async startExplanation() {
        const codeEditor = window.codeExplainer?.codeEditor;
        if (!codeEditor) {
            RAssistant.showToast('代码编辑器未初始化', 'error');
            return;
        }

        const code = codeEditor.getValue().trim();
        if (!code) {
            RAssistant.showToast('请输入要解释的代码', 'warning');
            return;
        }

        // 隐藏空状态，显示进度
        this.showProgress();
        this.updateButton('processing');

        try {
            await this.processor.startStream('/api/streaming/explain/', { code }, {
                onStart: (data) => {
                    this.updateProgress(0, 4, data.message);
                },
                onProgress: (data) => {
                    this.updateProgress(data.step, data.total, data.message);
                },
                onResult: (data) => {
                    this.showResult(data);
                },
                onError: (error) => {
                    this.showError(error.message);
                },
                onComplete: () => {
                    this.updateButton('complete');
                    RAssistant.showToast('代码解释完成！', 'success');
                }
            });
        } catch (error) {
            this.showError(error.message);
            this.updateButton('error');
        }
    }

    showProgress() {
        const emptyState = document.getElementById('emptyState');
        const progressElement = document.getElementById('streamProgress');
        
        if (emptyState) emptyState.style.display = 'none';
        if (progressElement) progressElement.style.display = 'block';
    }

    updateProgress(step, total, message) {
        const progressBar = document.getElementById('progressBar');
        const progressMessage = document.getElementById('progressMessage');
        const progressStep = document.getElementById('progressStep');
        const progressTotal = document.getElementById('progressTotal');

        if (progressBar) {
            const percentage = (step / total) * 100;
            progressBar.style.width = `${percentage}%`;
        }

        if (progressMessage) progressMessage.textContent = message;
        if (progressStep) progressStep.textContent = step;
        if (progressTotal) progressTotal.textContent = total;
    }

    showResult(data) {
        const streamingContent = document.getElementById('streamingContent');
        if (!streamingContent) return;

        const resultHTML = `
            <div class="explanation-result">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-success mb-0">
                        <i class="fas fa-check-circle me-2"></i>
                        解释完成
                    </h5>
                    <small class="text-muted">
                        处理时间: ${data.processing_time?.toFixed(2) || 0}秒
                    </small>
                </div>
                
                <div class="explanation-content markdown-content">
                    ${this.renderMarkdown(data.explanation || '解释内容生成失败')}
                </div>
                
                ${data.analysis ? this.renderAnalysis(data.analysis) : ''}
                
                <div class="action-buttons mt-3">
                    <button type="button" class="btn btn-outline-light btn-sm" onclick="streamExplainer.copyResult()">
                        <i class="fas fa-copy me-1"></i>复制解释
                    </button>
                    <button type="button" class="btn btn-outline-success btn-sm" onclick="streamExplainer.saveResult()">
                        <i class="fas fa-download me-1"></i>保存结果
                    </button>
                </div>
            </div>
        `;

        streamingContent.innerHTML = resultHTML;
        this.lastResult = data;
    }

    renderAnalysis(analysis) {
        if (!analysis || typeof analysis !== 'object') return '';

        return `
            <div class="analysis-section mt-4">
                <h6 class="text-info mb-3">
                    <i class="fas fa-chart-bar me-2"></i>
                    代码质量分析
                </h6>
                <div class="row">
                    <div class="col-md-8">
                        <div class="text-light">
                            ${analysis.summary || '分析结果不可用'}
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-value">${analysis.quality_score || '--'}</div>
                                <div class="text-muted small">质量分数</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${analysis.complexity || '--'}</div>
                                <div class="text-muted small">复杂度</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showError(message) {
        const streamingContent = document.getElementById('streamingContent');
        if (!streamingContent) return;

        streamingContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }

    updateButton(state) {
        const explainBtn = document.getElementById('explainBtn');
        if (!explainBtn) return;

        switch (state) {
            case 'processing':
                explainBtn.disabled = true;
                explainBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>解释中...';
                break;
            case 'complete':
            case 'error':
                explainBtn.disabled = false;
                explainBtn.innerHTML = '<i class="fas fa-brain me-2"></i>开始解释';
                break;
        }
    }

    renderMarkdown(text) {
        // 简单的markdown渲染
        return text
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\n/g, '<br>');
    }

    copyResult() {
        if (!this.lastResult) return;
        
        navigator.clipboard.writeText(this.lastResult.explanation).then(() => {
            RAssistant.showToast('解释内容已复制到剪贴板', 'success');
        }).catch(() => {
            RAssistant.showToast('复制失败', 'error');
        });
    }

    saveResult() {
        if (!this.lastResult) return;

        const content = `# R代码解释结果\n\n${this.lastResult.explanation}`;
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `r_code_explanation_${Date.now()}.md`;
        a.click();
        
        URL.revokeObjectURL(url);
        RAssistant.showToast('解释结果已保存', 'success');
    }
}

/**
 * 流式作业求解器
 */
class StreamingAnswerSolver {
    constructor() {
        this.processor = new StreamingProcessor();
        this.init();
    }

    init() {
        this.createProgressUI();
        this.setupEventListeners();
    }

    createProgressUI() {
        // 类似的进度UI，但针对作业求解进行调整
        const progressHTML = `
            <div id="answerStreamProgress" class="streaming-progress" style="display: none;">
                <div class="progress-header">
                    <h6 class="text-info mb-2">
                        <i class="fas fa-lightbulb me-2"></i>
                        AI正在为您求解问题
                    </h6>
                </div>
                <div class="progress-content">
                    <div class="progress mb-3" style="height: 8px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" 
                             id="answerProgressBar" style="width: 0%"></div>
                    </div>
                    <div class="progress-message">
                        <span id="answerProgressMessage">准备中...</span>
                        <span class="float-end text-muted">
                            <span id="answerProgressStep">0</span>/<span id="answerProgressTotal">6</span>
                        </span>
                    </div>
                </div>
                <div class="streaming-content mt-3" id="answerStreamingContent">
                    <!-- 流式内容将在这里显示 -->
                </div>
            </div>
        `;

        // 添加到答案结果容器
        const answerContainer = document.querySelector('.answer-results');
        if (answerContainer) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = progressHTML;
            answerContainer.appendChild(tempDiv.firstElementChild);
        }
    }

    setupEventListeners() {
        // 监听表单提交
        const answerForm = document.querySelector('form[method="post"]');
        if (answerForm) {
            answerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startSolving();
            });
        }
    }

    async startSolving() {
        const problemTextarea = document.querySelector('textarea[name="problem"]');
        const fileInput = document.querySelector('input[name="uploaded_files"]');
        
        if (!problemTextarea || !problemTextarea.value.trim()) {
            RAssistant.showToast('请输入要求解的问题', 'warning');
            return;
        }

        const formData = {
            problem: problemTextarea.value.trim(),
            uploaded_files: []
        };

        // 处理文件上传（简化版）
        if (fileInput && fileInput.files.length > 0) {
            // 这里应该处理文件上传，但为了简化，暂时跳过
            RAssistant.showToast('文件上传功能正在完善中', 'info');
        }

        this.showProgress();
        this.updateButton('processing');

        try {
            await this.processor.startStream('/api/streaming/answer/', formData, {
                onStart: (data) => {
                    this.updateProgress(0, 6, data.message);
                },
                onProgress: (data) => {
                    this.updateProgress(data.step, data.total, data.message);
                },
                onResult: (data) => {
                    this.showResult(data);
                },
                onError: (error) => {
                    this.showError(error.message);
                },
                onComplete: () => {
                    this.updateButton('complete');
                    RAssistant.showToast('问题求解完成！', 'success');
                }
            });
        } catch (error) {
            this.showError(error.message);
            this.updateButton('error');
        }
    }

    showProgress() {
        const emptyState = document.getElementById('emptyState');
        const progressElement = document.getElementById('answerStreamProgress');
        
        if (emptyState) emptyState.style.display = 'none';
        if (progressElement) progressElement.style.display = 'block';
    }

    updateProgress(step, total, message) {
        const progressBar = document.getElementById('answerProgressBar');
        const progressMessage = document.getElementById('answerProgressMessage');
        const progressStep = document.getElementById('answerProgressStep');
        const progressTotal = document.getElementById('answerProgressTotal');

        if (progressBar) {
            const percentage = (step / total) * 100;
            progressBar.style.width = `${percentage}%`;
        }

        if (progressMessage) progressMessage.textContent = message;
        if (progressStep) progressStep.textContent = step;
        if (progressTotal) progressTotal.textContent = total;
    }

    showResult(data) {
        const streamingContent = document.getElementById('answerStreamingContent');
        if (!streamingContent) return;

        let solutionsHTML = '';
        if (data.solutions && data.solutions.length > 0) {
            solutionsHTML = data.solutions.map((solution, index) => `
                <div class="solution-card mb-4">
                    <div class="solution-header">
                        <h5 class="text-primary mb-2">
                            <i class="fas fa-lightbulb me-2"></i>
                            ${solution.title || `解决方案 ${index + 1}`}
                        </h5>
                    </div>
                    
                    <div class="code-section bg-dark bg-opacity-30 rounded-3 p-3 mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="text-light">
                                <i class="fab fa-r-project me-2 text-info"></i>
                                R代码
                            </span>
                            <button class="btn btn-outline-light btn-sm copy-code-btn" 
                                    onclick="streamAnswerSolver.copyCode('${index}')">
                                <i class="fas fa-copy me-1"></i>复制
                            </button>
                        </div>
                        <pre class="mb-0"><code class="language-r">${solution.code}</code></pre>
                    </div>
                    
                    <div class="explanation-section bg-secondary bg-opacity-20 rounded-3 p-3">
                        <h6 class="text-info mb-2">
                            <i class="fas fa-info-circle me-2"></i>
                            详细解释
                        </h6>
                        <div class="explanation-content">
                            ${this.renderMarkdown(solution.explanation)}
                        </div>
                    </div>
                    
                    ${solution.filename ? `
                        <div class="mt-2">
                            <small class="text-muted">
                                <i class="fas fa-file-code me-1"></i>
                                建议文件名: <code class="text-warning">${solution.filename}</code>
                            </small>
                        </div>
                    ` : ''}
                </div>
            `).join('<hr class="border-secondary my-4">');
        }

        const resultHTML = `
            <div class="answer-result">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="text-success mb-0">
                        <i class="fas fa-check-circle me-2"></i>
                        求解完成
                    </h5>
                    <small class="text-muted">
                        处理时间: ${data.processing_time?.toFixed(2) || 0}秒
                    </small>
                </div>
                
                ${data.answer_result ? `
                    <div class="answer-summary mb-4">
                        <h6 class="text-warning mb-2">
                            <i class="fas fa-lightbulb me-2"></i>
                            解答摘要
                        </h6>
                        <div class="markdown-content">
                            ${this.renderMarkdown(data.answer_result)}
                        </div>
                    </div>
                ` : ''}
                
                ${solutionsHTML}
                
                <div class="action-buttons mt-3">
                    <button type="button" class="btn btn-outline-light btn-sm" onclick="streamAnswerSolver.saveAllSolutions()">
                        <i class="fas fa-download me-1"></i>保存所有解决方案
                    </button>
                </div>
            </div>
        `;

        streamingContent.innerHTML = resultHTML;
        this.lastResult = data;
    }

    showError(message) {
        const streamingContent = document.getElementById('answerStreamingContent');
        if (!streamingContent) return;

        streamingContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }

    updateButton(state) {
        const solveBtn = document.querySelector('button[type="submit"]');
        if (!solveBtn) return;

        switch (state) {
            case 'processing':
                solveBtn.disabled = true;
                solveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>求解中...';
                break;
            case 'complete':
            case 'error':
                solveBtn.disabled = false;
                solveBtn.innerHTML = '<i class="fas fa-lightbulb me-2"></i>开始求解';
                break;
        }
    }

    renderMarkdown(text) {
        // 复用markdown渲染逻辑
        return text
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/\n/g, '<br>');
    }

    copyCode(index) {
        if (!this.lastResult || !this.lastResult.solutions || !this.lastResult.solutions[index]) return;
        
        const code = this.lastResult.solutions[index].code;
        navigator.clipboard.writeText(code).then(() => {
            RAssistant.showToast('代码已复制到剪贴板', 'success');
        }).catch(() => {
            RAssistant.showToast('复制失败', 'error');
        });
    }

    saveAllSolutions() {
        if (!this.lastResult || !this.lastResult.solutions) return;

        const content = this.lastResult.solutions.map((solution, index) => `
# 解决方案 ${index + 1}: ${solution.title}

## R代码
\`\`\`r
${solution.code}
\`\`\`

## 详细解释
${solution.explanation}

---
        `).join('\n');

        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `r_solutions_${Date.now()}.md`;
        a.click();
        
        URL.revokeObjectURL(url);
        RAssistant.showToast('所有解决方案已保存', 'success');
    }
}

// 全局实例
let streamExplainer, streamAnswerSolver;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 根据页面类型初始化相应的流式处理器
    if (document.querySelector('#explainBtn')) {
        streamExplainer = new StreamingCodeExplainer();
    }
    
    if (document.querySelector('textarea[name="problem"]')) {
        streamAnswerSolver = new StreamingAnswerSolver();
    }
});