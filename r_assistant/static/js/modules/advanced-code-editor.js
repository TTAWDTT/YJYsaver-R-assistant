/**
 * Advanced Code Editor - VSCode-style 代码编辑器
 * 解决行号匹配、符号显示等问题，并提供增强的编辑体验
 * Version: 2.1 - 优化行号显示
 */

class AdvancedCodeEditor {
    constructor(containerSelector, options = {}) {
        this.container = document.querySelector(containerSelector);
        this.options = {
            language: 'r',
            theme: 'vs-dark',
            lineNumbers: true,
            wordWrap: true,
            minimap: false,
            fontSize: 14,
            fontFamily: 'Monaco, "Cascadia Code", "SF Mono", Consolas, "Liberation Mono", Menlo, Courier, monospace',
            insertSpaces: true,
            tabSize: 2,
            detectIndentation: true,
            renderWhitespace: 'selection',
            renderControlCharacters: true,
            formatOnPaste: true,
            formatOnType: true,
            autoIndent: 'advanced',
            bracketPairColorization: { enabled: true },
            guides: { bracketPairs: 'active', indentation: true },
            suggestOnTriggerCharacters: true,
            quickSuggestions: { other: true, comments: false, strings: false },
            ...options
        };
        
        this.editor = null;
        this.model = null;
        this.selectedLines = new Set();
        this.symbolMap = this.initializeSymbolMap();
        
        this.init();
    }
    
    initializeSymbolMap() {
        // R语言特殊符号映射表，解决符号显示问题
        return {
            // 赋值操作符
            '<-': '←',
            '->': '→',
            '<<-': '⟸',
            '->>': '⟹',
            
            // 逻辑操作符
            '<=': '≤',
            '>=': '≥',
            '!=': '≠',
            '==': '≡',
            '%in%': '∈',
            '%!in%': '∉',
            
            // 管道操作符
            '%>%': '▷',
            '|>': '▶',
            
            // 数学符号
            'Inf': '∞',
            '-Inf': '-∞',
            'pi': 'π',
            'alpha': 'α',
            'beta': 'β',
            'gamma': 'γ',
            'delta': 'δ',
            'epsilon': 'ε',
            'lambda': 'λ',
            'mu': 'μ',
            'sigma': 'σ',
            'theta': 'θ',
            
            // 统计符号
            'mean': 'x̄',
            'sum': '∑',
            'sqrt': '√',
            
            // 其他常用符号
            '...': '…',
            'NULL': '∅',
            'NA': '⊘',
            'NaN': '⌀'
        };
    }
    
    async init() {
        try {
            // 检查 Monaco Editor 是否可用
            if (typeof monaco === 'undefined') {
                await this.loadMonacoEditor();
            }
            
            this.setupContainer();
            this.createEditor();
            this.setupEventListeners();
            this.setupSymbolReplacement();
            this.setupLineSelection();
            this.setupErrorHandling();
            
        } catch (error) {
            console.warn('Monaco Editor 不可用，使用增强的 textarea 编辑器:', error);
            this.createFallbackEditor();
        }
    }
    
    async loadMonacoEditor() {
        return new Promise((resolve, reject) => {
            // 检查是否已经加载了Monaco
            if (typeof require !== 'undefined' && typeof monaco !== 'undefined') {
                resolve();
                return;
            }
            
            // 设置5秒超时
            const timeout = setTimeout(() => {
                reject(new Error('Monaco Editor加载超时'));
            }, 5000);
            
            // 创建脚本元素
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.1/min/vs/loader.js';
            script.onload = () => {
                clearTimeout(timeout);
                // 配置require.js
                if (typeof require !== 'undefined') {
                    require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.1/min/vs' }});
                    require(['vs/editor/editor.main'], () => {
                        resolve();
                    });
                } else {
                    // 如果require未定义，尝试直接加载编辑器
                    const editorScript = document.createElement('script');
                    editorScript.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.1/min/vs/editor/editor.main.js';
                    editorScript.onload = () => {
                        resolve();
                    };
                    editorScript.onerror = () => {
                        clearTimeout(timeout);
                        reject(new Error('Monaco Editor主文件加载失败'));
                    };
                    document.head.appendChild(editorScript);
                }
            };
            script.onerror = () => {
                clearTimeout(timeout);
                console.warn('Monaco Editor CDN不可用，使用备用编辑器');
                reject(new Error('Monaco Editor CDN加载失败'));
            };
            document.head.appendChild(script);
        });
    }
    
    setupContainer() {
        this.container.innerHTML = '';
        this.container.className = 'advanced-code-editor';
        this.container.style.cssText = `
            position: relative;
            width: 100%;
            height: 400px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            overflow: hidden;
            background: #1e1e1e;
            font-family: ${this.options.fontFamily};
        `;
    }
    
    createEditor() {
        try {
            // 配置 R 语言支持
            if (monaco.languages) {
                monaco.languages.register({ id: 'r' });
                
                // 设置 R 语言语法高亮
                monaco.languages.setMonarchTokensProvider('r', this.getRSyntaxDefinition());
                
                // 设置自动补全
                monaco.languages.registerCompletionItemProvider('r', this.getRCompletionProvider());
            }
            
            // 创建编辑器
            this.editor = monaco.editor.create(this.container, {
                value: '',
                language: 'r',
                theme: this.options.theme,
                fontSize: this.options.fontSize,
                fontFamily: this.options.fontFamily,
                
                // 行号设置 - 模仿VS Code
                lineNumbers: 'on',              // 显示行号
                lineNumbersMinChars: 4,         // 行号最小字符数，为较大文件留出空间
                lineDecorationsWidth: 10,       // 行装饰宽度
                glyphMargin: true,              // 显示字形边距，用于断点等
                folding: true,                  // 启用代码折叠
                foldingStrategy: 'indentation', // 使用缩进策略进行折叠
                
                // 行高亮设置
                lineHighlightBackground: 'rgba(255, 255, 255, 0.04)',
                renderLineHighlight: 'all',
                cursorBlinking: 'blink',        // 光标闪烁
                cursorSmoothCaretAnimation: true, // 平滑光标动画
                
                // 布局和滚动
                wordWrap: this.options.wordWrap ? 'on' : 'off',
                minimap: { enabled: this.options.minimap },
                scrollBeyondLastLine: false,
                automaticLayout: true,
                scrollbar: {
                    vertical: 'visible',
                    horizontal: 'visible',
                    useShadows: false,
                    verticalHasArrows: false,
                    horizontalHasArrows: false,
                    verticalScrollbarSize: 14,
                    horizontalScrollbarSize: 14
                },
                
                // 渲染设置
                renderWhitespace: this.options.renderWhitespace,
                renderControlCharacters: this.options.renderControlCharacters,
                renderIndentGuides: true,       // 显示缩进引导线
                rulers: [],                     // 可以添加标尺线
                
                // 格式化和编辑
                formatOnPaste: this.options.formatOnPaste,
                formatOnType: this.options.formatOnType,
                autoIndent: this.options.autoIndent,
                bracketPairColorization: this.options.bracketPairColorization,
                guides: this.options.guides,
                
                // 智能提示
                suggestOnTriggerCharacters: this.options.suggestOnTriggerCharacters,
                quickSuggestions: this.options.quickSuggestions,
                parameterHints: { enabled: true },
                
                // 制表符设置
                tabSize: this.options.tabSize,
                insertSpaces: this.options.insertSpaces,
                detectIndentation: this.options.detectIndentation,
                
                // 其他VS Code风格设置
                multiCursorModifier: 'ctrlCmd',  // 多光标修饰键
                wordBasedSuggestions: true,      // 基于单词的建议
                contextmenu: true,               // 右键菜单
                mouseWheelZoom: true,            // 鼠标滚轮缩放
                links: true,                     // 启用链接检测
                colorDecorators: true,           // 颜色装饰器
                lightbulb: { enabled: true },    // 显示灯泡提示
                codeActionsOnSave: {},           // 保存时的代码操作
                showFoldingControls: 'always',   // 始终显示折叠控件
                smoothScrolling: true,           // 平滑滚动
                cursorWidth: 2,                  // 光标宽度
                letterSpacing: 0,                // 字母间距
                fontLigatures: true,             // 字体连字
                disableLayerHinting: false,      // 启用图层提示
                hideCursorInOverviewRuler: false, // 在概览标尺中显示光标
                overviewRulerBorder: false,      // 概览标尺边框
                overviewRulerLanes: 3            // 概览标尺车道数
            });
            
            this.model = this.editor.getModel();
        } catch (error) {
            console.error('创建Monaco编辑器失败:', error);
            throw error;
        }
    }
    
    createFallbackEditor() {
        const fallbackContainer = document.createElement('div');
        fallbackContainer.className = 'fallback-code-editor';
        fallbackContainer.innerHTML = `
            <div class="editor-toolbar">
                <div class="toolbar-left">
                    <button type="button" class="btn-tool" onclick="this.parentNode.parentNode.parentNode.querySelector('textarea').value = ''">
                        <i class="fas fa-trash"></i> 清空
                    </button>
                    <button type="button" class="btn-tool" id="symbol-toggle">
                        <i class="fas fa-font"></i> 符号显示
                    </button>
                    <button type="button" class="btn-tool">
                        <i class="fas fa-indent"></i> 格式化
                    </button>
                </div>
                <div class="toolbar-right">
                    <span class="editor-info">R Language</span>
                </div>
            </div>
            <div class="editor-content">
                <div class="line-numbers-container">
                    <div class="line-numbers" id="line-numbers"></div>
                </div>
                <div class="code-input-container">
                    <textarea 
                        class="code-textarea" 
                        id="code-textarea"
                        spellcheck="false"
                        placeholder="在此粘贴您的R语言代码..."
                        data-gramm="false"
                    ></textarea>
                    <div class="symbol-overlay" id="symbol-overlay"></div>
                </div>
            </div>
            <div class="editor-status">
                <div class="status-left">
                    <span id="cursor-position">Ln 1, Col 1</span>
                    <span id="selection-info"></span>
                </div>
                <div class="status-right">
                    <span id="line-count">1 line</span>
                    <span id="encoding">UTF-8</span>
                </div>
            </div>
        `;
        
        this.container.appendChild(fallbackContainer);
        this.setupFallbackEditor();
    }
    
    setupFallbackEditor() {
        const textarea = this.container.querySelector('#code-textarea');
        const lineNumbers = this.container.querySelector('#line-numbers');
        const symbolOverlay = this.container.querySelector('#symbol-overlay');
        const cursorPosition = this.container.querySelector('#cursor-position');
        const selectionInfo = this.container.querySelector('#selection-info');
        const lineCount = this.container.querySelector('#line-count');
        
        let symbolMode = false;
        
        // 创建样式
        const style = document.createElement('style');
        style.textContent = `
            .fallback-code-editor {
                display: flex;
                flex-direction: column;
                height: 100%;
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: ${this.options.fontFamily};
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #333;
            }
            
            .editor-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                background: #2d2d30;
                border-bottom: 1px solid #3e3e42;
                font-size: 12px;
            }
            
            .toolbar-left, .toolbar-right {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .btn-tool {
                background: transparent;
                border: 1px solid transparent;
                color: #cccccc;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 11px;
                transition: all 0.2s;
            }
            
            .btn-tool:hover {
                background: #3e3e42;
                border-color: #4a4a4a;
            }
            
            .btn-tool.active {
                background: #007acc;
                color: white;
            }
            
            .editor-content {
                display: flex;
                flex: 1;
                overflow: hidden;
            }
            
            .line-numbers-container {
                background: #1e1e1e;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                user-select: none;
                display: flex;
                flex-direction: column;
                flex-shrink: 0;
            }
            
            .line-numbers {
                font-family: 'Consolas', 'SF Mono', Monaco, 'Cascadia Code', monospace;
                font-size: 13px;
                line-height: 18px;
                color: #858585;
                text-align: right;
                padding: 10px 8px 10px 4px;
                overflow: hidden;
                white-space: nowrap;
                min-width: 35px;
                background: #1e1e1e;
                margin: 0;
            }
            
            .line-numbers .line-number {
                display: block;
                height: 18px;
                line-height: 18px;
                cursor: pointer;
                padding: 0 4px 0 0;
                margin: 0;
                transition: all 0.1s;
                white-space: pre;
                text-align: right;
            }
            
            .line-numbers .line-number:hover {
                color: #c6c6c6;
                background-color: rgba(255, 255, 255, 0.05);
            }
            
            .line-numbers .line-number.selected {
                background-color: rgba(0, 122, 204, 0.3);
                color: #ffffff;
            }
            
            .code-input-container {
                flex: 1;
                position: relative;
                overflow: hidden;
            }
            
            .code-textarea {
                width: 100%;
                height: 100%;
                background: transparent;
                border: none;
                color: #d4d4d4;
                font-family: 'Consolas', 'SF Mono', Monaco, 'Cascadia Code', monospace;
                font-size: 13px;
                line-height: 18px;
                padding: 10px 12px;
                resize: none;
                overflow: auto;
                white-space: pre;
                tab-size: 4;
                outline: none;
                margin: 0;
            }
            
            .code-textarea::placeholder {
                color: #6a6a6a;
                font-style: italic;
            }
            
            .editor-status {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 4px 12px;
                background: #007acc;
                color: white;
                font-size: 11px;
                font-family: 'Consolas', 'SF Mono', Monaco, monospace;
            }
            
            .status-left, .status-right {
                display: flex;
                gap: 12px;
            }
                border-bottom: 1px solid #3e3e42;
            }
            
            .toolbar-left, .toolbar-right {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .btn-tool {
                background: none;
                border: 1px solid #464647;
                color: #cccccc;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: all 0.2s ease;
            }
            
            .btn-tool:hover {
                background: #464647;
                border-color: #6c6c6c;
            }
            
            .editor-info {
                font-size: 12px;
                color: #cccccc;
                background: #0e639c;
                padding: 2px 8px;
                border-radius: 12px;
            }
            
            .editor-content {
                flex: 1;
                display: flex;
                position: relative;
                overflow: hidden;
            }
            
            .line-numbers-container {
                background: #1e1e1e;
                border-right: 1px solid #3e3e42;
                user-select: none;
                min-width: 50px;
            }
            
            .line-numbers {
                font-family: ${this.options.fontFamily};
                font-size: 14px;
                line-height: 20px;
                color: #858585;
                text-align: right;
                padding: 10px 8px;
                white-space: pre;
                position: relative;
            }
            
            .line-number {
                display: block;
                height: 20px;
                cursor: pointer;
                padding: 0 4px;
                border-radius: 2px;
                transition: all 0.2s ease;
            }
            
            .line-number:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
            }
            
            .line-number.selected {
                background: #094771;
                color: #ffffff;
            }
            
            .code-input-container {
                flex: 1;
                position: relative;
            }
            
            .code-textarea {
                width: 100%;
                height: 100%;
                background: transparent;
                border: none;
                outline: none;
                resize: none;
                font-family: ${this.options.fontFamily};
                font-size: 14px;
                line-height: 20px;
                color: #d4d4d4;
                padding: 10px;
                white-space: pre;
                overflow-wrap: normal;
                overflow-x: auto;
                z-index: 1;
                position: relative;
            }
            
            .symbol-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                font-family: ${this.options.fontFamily};
                font-size: 14px;
                line-height: 20px;
                color: #569cd6;
                padding: 10px;
                white-space: pre;
                z-index: 2;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .symbol-overlay.active {
                opacity: 1;
            }
            
            .editor-status {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 4px 12px;
                background: #007acc;
                color: white;
                font-size: 12px;
            }
            
            .status-left, .status-right {
                display: flex;
                gap: 16px;
            }
            
            /* 语法高亮样式 */
            .syntax-keyword { color: #569cd6; }
            .syntax-string { color: #ce9178; }
            .syntax-number { color: #b5cea8; }
            .syntax-comment { color: #6a9955; font-style: italic; }
            .syntax-operator { color: #d4d4d4; }
            .syntax-function { color: #dcdcaa; }
            .syntax-variable { color: #9cdcfe; }
        `;
        document.head.appendChild(style);
        
        // 更新行号 - 确保每行都显示
        function updateLineNumbers() {
            const lines = textarea.value.split('\n');
            const maxLineNum = lines.length;
            
            // 生成行号HTML，确保每一行都有对应的行号
            const lineNumbersHtml = lines.map((line, index) => {
                const lineNum = index + 1;
                const isSelected = this.selectedLines?.has(lineNum);
                // 使用简单的数字，不需要特殊填充
                return `<div class="line-number ${isSelected ? 'selected' : ''}" data-line="${lineNum}">${lineNum}</div>`;
            }).join('');
            
            lineNumbers.innerHTML = lineNumbersHtml;
            
            // 动态调整行号容器宽度，根据最大行号的字符数
            const maxWidth = Math.max(32, maxLineNum.toString().length * 8 + 16);
            lineNumbers.style.minWidth = maxWidth + 'px';
            
            // 更新状态栏
            if (lineCount) {
                lineCount.textContent = `${lines.length} ${lines.length === 1 ? 'line' : 'lines'}`;
            }
            
            // 同步滚动
            if (this.syncLineNumbersScroll) {
                this.syncLineNumbersScroll();
            }
        }
        
        // 更新光标位置
        function updateCursorPosition() {
            const selectionStart = textarea.selectionStart;
            const selectionEnd = textarea.selectionEnd;
            const text = textarea.value;
            
            const beforeCursor = text.substring(0, selectionStart);
            const lines = beforeCursor.split('\n');
            const line = lines.length;
            const column = lines[lines.length - 1].length + 1;
            
            cursorPosition.textContent = `Ln ${line}, Col ${column}`;
            
            if (selectionStart !== selectionEnd) {
                const selectedText = text.substring(selectionStart, selectionEnd);
                const selectedLines = selectedText.split('\n').length;
                const selectedChars = selectedText.length;
                selectionInfo.textContent = `(${selectedChars} selected)`;
            } else {
                selectionInfo.textContent = '';
            }
        }
        
        // 符号替换
        function updateSymbolOverlay() {
            if (!symbolMode) {
                symbolOverlay.classList.remove('active');
                return;
            }
            
            let content = textarea.value;
            for (const [original, replacement] of Object.entries(this.symbolMap)) {
                content = content.replace(new RegExp(escapeRegex(original), 'g'), replacement);
            }
            symbolOverlay.textContent = content;
            symbolOverlay.classList.add('active');
        }
        
        function escapeRegex(string) {
            return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }
        
        // 事件监听 - 确保行号实时更新
        textarea.addEventListener('input', () => {
            updateLineNumbers.call(this);
            updateCursorPosition();
            updateSymbolOverlay.call(this);
        });
        
        textarea.addEventListener('paste', () => {
            // 延迟执行，确保内容已经粘贴
            setTimeout(() => {
                updateLineNumbers.call(this);
                updateCursorPosition();
            }, 10);
        });
        
        textarea.addEventListener('keydown', (e) => {
            // 在回车键、删除键等操作后更新行号
            if (e.key === 'Enter' || e.key === 'Backspace' || e.key === 'Delete') {
                setTimeout(() => {
                    updateLineNumbers.call(this);
                    updateCursorPosition();
                }, 10);
            }
        });
        
        // 滚动和选择事件
        textarea.addEventListener('scroll', () => {
            this.syncLineNumbersScroll();
        });
        
        // 同步行号滚动
        this.syncLineNumbersScroll = function() {
            if (lineNumbers && textarea) {
                lineNumbers.scrollTop = textarea.scrollTop;
            }
        };
        
        textarea.addEventListener('selectionchange', updateCursorPosition);
        textarea.addEventListener('keyup', updateCursorPosition);
        textarea.addEventListener('mouseup', updateCursorPosition);
        
        // 行号点击选择功能
        lineNumbers.addEventListener('click', (e) => {
            if (e.target.classList.contains('line-number')) {
                const lineNum = parseInt(e.target.dataset.line);
                this.toggleLineSelection(lineNum);
                updateLineNumbers.call(this);
                
                // 选中对应行的文本
                this.selectLine(lineNum);
            }
        });
        
        // 滚动同步 - 双向同步
        textarea.addEventListener('scroll', () => {
            this.syncLineNumbersScroll();
        });
        
        // 确保行号区域也能同步滚动
        lineNumbers.addEventListener('scroll', () => {
            if (Math.abs(textarea.scrollTop - lineNumbers.scrollTop) > 1) {
                textarea.scrollTop = lineNumbers.scrollTop;
            }
        });
        
        // 工具栏功能
        this.container.querySelector('#symbol-toggle').onclick = () => {
            symbolMode = !symbolMode;
            const btn = this.container.querySelector('#symbol-toggle');
            btn.classList.toggle('active', symbolMode);
            updateSymbolOverlay.call(this);
        };
        
        // 初始化
        updateLineNumbers.call(this);
        updateCursorPosition();
        
        // 保存引用
        this.textarea = textarea;
        this.updateLineNumbers = updateLineNumbers.bind(this);
        this.updateSymbolOverlay = updateSymbolOverlay.bind(this);
    }
    
    getRSyntaxDefinition() {
        return {
            tokenizer: {
                root: [
                    // 注释
                    [/#.*$/, 'comment'],
                    
                    // 字符串
                    [/"([^"\\]|\\.)*$/, 'string.invalid'],
                    [/"/, 'string', '@string_double'],
                    [/'([^'\\]|\\.)*$/, 'string.invalid'],
                    [/'/, 'string', '@string_single'],
                    
                    // 数字
                    [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
                    [/\d+[eE][\-+]?\d+/, 'number.float'],
                    [/\d+/, 'number'],
                    
                    // 关键字
                    [/\b(if|else|for|while|function|return|TRUE|FALSE|NULL|NA|NaN|Inf)\b/, 'keyword'],
                    
                    // 操作符
                    [/(<-|->|<<-|->>|%>%|%in%|%!in%|==|!=|<=|>=|&&|\|\|)/, 'operator'],
                    
                    // 函数名
                    [/[a-zA-Z_][a-zA-Z0-9_.]*(?=\s*\()/, 'entity.name.function'],
                    
                    // 变量名
                    [/[a-zA-Z_][a-zA-Z0-9_.]*/, 'variable'],
                    
                    // 分隔符
                    [/[{}()\[\]]/, '@brackets'],
                    [/[;,.]/, 'delimiter'],
                ],
                
                string_double: [
                    [/[^\\"]+/, 'string'],
                    [/\\./, 'string.escape'],
                    [/"/, 'string', '@pop']
                ],
                
                string_single: [
                    [/[^\\']+/, 'string'],
                    [/\\./, 'string.escape'],
                    [/'/, 'string', '@pop']
                ]
            }
        };
    }
    
    getRCompletionProvider() {
        const rKeywords = [
            'if', 'else', 'for', 'while', 'function', 'return', 'TRUE', 'FALSE', 
            'NULL', 'NA', 'NaN', 'Inf', 'library', 'require', 'data.frame',
            'list', 'vector', 'matrix', 'array', 'factor', 'character', 'numeric',
            'logical', 'integer', 'double', 'complex', 'raw'
        ];
        
        const rFunctions = [
            'abs', 'acos', 'asin', 'atan', 'ceiling', 'cos', 'exp', 'floor',
            'log', 'max', 'min', 'round', 'sin', 'sqrt', 'tan', 'mean', 'median',
            'sum', 'length', 'nrow', 'ncol', 'dim', 'names', 'colnames', 'rownames',
            'head', 'tail', 'summary', 'str', 'class', 'typeof', 'is.na', 'is.null',
            'paste', 'paste0', 'cat', 'print', 'sprintf', 'substr', 'nchar',
            'read.csv', 'write.csv', 'read.table', 'write.table'
        ];
        
        return {
            provideCompletionItems: (model, position) => {
                const suggestions = [];
                
                // 关键字建议
                rKeywords.forEach(keyword => {
                    suggestions.push({
                        label: keyword,
                        kind: monaco.languages.CompletionItemKind.Keyword,
                        insertText: keyword
                    });
                });
                
                // 函数建议
                rFunctions.forEach(func => {
                    suggestions.push({
                        label: func,
                        kind: monaco.languages.CompletionItemKind.Function,
                        insertText: func + '()',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
                    });
                });
                
                return { suggestions };
            }
        };
    }
    
    setupEventListeners() {
        if (!this.editor || !this.model) return;
        
        try {
            // 内容变化监听
            this.model.onDidChangeContent(() => {
                this.onContentChange();
            });
            
            // 选择变化监听
            this.editor.onDidChangeCursorSelection(() => {
                this.onSelectionChange();
            });
            
            // 键盘快捷键
            if (this.editor.addCommand && monaco.KeyMod && monaco.KeyCode) {
                this.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyK, () => {
                    this.formatCode();
                });
                
                this.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyD, () => {
                    this.duplicateLine();
                });
            }
        } catch (error) {
            console.warn('设置编辑器事件监听器失败:', error);
        }
    }
    
    setupSymbolReplacement() {
        // 实时符号替换 (可选功能)
        if (this.options.enableSymbolReplacement) {
            this.model.onDidChangeContent(() => {
                this.replaceSymbols();
            });
        }
    }
    
    setupLineSelection() {
        if (!this.editor) return;
        
        // 行号点击选择
        this.editor.onMouseDown((e) => {
            if (e.target.type === monaco.editor.MouseTargetType.GUTTER_LINE_NUMBERS) {
                const lineNumber = e.target.position.lineNumber;
                this.toggleLineSelection(lineNumber);
            }
        });
    }
    
    setupErrorHandling() {
        // 语法错误检查
        this.model.onDidChangeContent(() => {
            this.checkSyntaxErrors();
        });
    }
    
    onContentChange() {
        // 触发自定义事件
        this.container.dispatchEvent(new CustomEvent('contentChange', {
            detail: { content: this.getValue() }
        }));
    }
    
    onSelectionChange() {
        // 触发选择变化事件
        const selection = this.editor?.getSelection();
        this.container.dispatchEvent(new CustomEvent('selectionChange', {
            detail: { selection }
        }));
    }
    
    toggleLineSelection(lineNumber) {
        if (this.selectedLines.has(lineNumber)) {
            this.selectedLines.delete(lineNumber);
        } else {
            this.selectedLines.add(lineNumber);
        }
        
        this.updateLineHighlights();
        this.onSelectionChange();
    }
    
    selectLine(lineNumber) {
        if (this.editor) {
            // Monaco Editor: 选中指定行
            const range = new monaco.Range(lineNumber, 1, lineNumber, Number.MAX_SAFE_INTEGER);
            this.editor.setSelection(range);
            this.editor.revealLineInCenter(lineNumber);
        } else if (this.textarea) {
            // 备用编辑器: 选中指定行
            const lines = this.textarea.value.split('\n');
            if (lineNumber > 0 && lineNumber <= lines.length) {
                let start = 0;
                for (let i = 0; i < lineNumber - 1; i++) {
                    start += lines[i].length + 1; // +1 for newline
                }
                const end = start + lines[lineNumber - 1].length;
                
                this.textarea.focus();
                this.textarea.setSelectionRange(start, end);
                
                // 滚动到选中行
                const lineHeight = parseInt(window.getComputedStyle(this.textarea).lineHeight) || 18;
                const scrollTop = (lineNumber - 1) * lineHeight - (this.textarea.clientHeight / 2);
                this.textarea.scrollTop = Math.max(0, scrollTop);
            }
        }
    }
    
    updateLineHighlights() {
        if (!this.editor) return;
        
        const decorations = Array.from(this.selectedLines).map(lineNumber => ({
            range: new monaco.Range(lineNumber, 1, lineNumber, 1),
            options: {
                isWholeLine: true,
                className: 'selected-line-highlight',
                marginClassName: 'selected-line-margin'
            }
        }));
        
        this.editor.deltaDecorations([], decorations);
    }
    
    formatCode() {
        if (this.editor) {
            this.editor.getAction('editor.action.formatDocument').run();
        } else if (this.textarea) {
            // 简单的格式化逻辑
            const content = this.textarea.value;
            const formatted = this.simpleFormatR(content);
            this.textarea.value = formatted;
            this.updateLineNumbers();
        }
    }
    
    simpleFormatR(code) {
        // 简单的R代码格式化
        return code
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .join('\n');
    }
    
    duplicateLine() {
        if (!this.editor) return;
        
        const position = this.editor.getPosition();
        const lineContent = this.model.getLineContent(position.lineNumber);
        
        this.editor.executeEdits('duplicate-line', [{
            range: new monaco.Range(position.lineNumber, this.model.getLineMaxColumn(position.lineNumber), position.lineNumber, this.model.getLineMaxColumn(position.lineNumber)),
            text: '\n' + lineContent
        }]);
    }
    
    replaceSymbols() {
        if (!this.editor) return;
        
        const content = this.model.getValue();
        let newContent = content;
        
        for (const [original, replacement] of Object.entries(this.symbolMap)) {
            newContent = newContent.replace(new RegExp(escapeRegex(original), 'g'), replacement);
        }
        
        if (newContent !== content) {
            this.model.setValue(newContent);
        }
    }
    
    checkSyntaxErrors() {
        // R语法检查 (简化版)
        const content = this.getValue();
        const errors = this.validateRSyntax(content);
        
        if (this.editor && errors.length > 0) {
            const markers = errors.map(error => ({
                severity: monaco.MarkerSeverity.Error,
                startLineNumber: error.line,
                startColumn: error.column,
                endLineNumber: error.line,
                endColumn: error.column + error.length,
                message: error.message
            }));
            
            monaco.editor.setModelMarkers(this.model, 'r-syntax', markers);
        }
    }
    
    validateRSyntax(code) {
        const errors = [];
        const lines = code.split('\n');
        
        lines.forEach((line, index) => {
            // 简单的语法检查
            const brackets = this.checkBrackets(line);
            if (brackets.error) {
                errors.push({
                    line: index + 1,
                    column: brackets.position,
                    length: 1,
                    message: brackets.message
                });
            }
        });
        
        return errors;
    }
    
    checkBrackets(line) {
        const stack = [];
        const pairs = { '(': ')', '[': ']', '{': '}' };
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if ('([{'.includes(char)) {
                stack.push({ char, pos: i });
            } else if (')]}'.includes(char)) {
                if (stack.length === 0) {
                    return { error: true, position: i, message: 'Unexpected closing bracket' };
                }
                const last = stack.pop();
                if (pairs[last.char] !== char) {
                    return { error: true, position: i, message: 'Mismatched brackets' };
                }
            }
        }
        
        if (stack.length > 0) {
            return { error: true, position: stack[0].pos, message: 'Unclosed bracket' };
        }
        
        return { error: false };
    }
    
    // 公共接口方法
    getValue() {
        if (this.editor) {
            return this.model.getValue();
        } else if (this.textarea) {
            return this.textarea.value;
        }
        return '';
    }
    
    setValue(value) {
        if (this.editor) {
            this.model.setValue(value);
        } else if (this.textarea) {
            this.textarea.value = value;
            this.updateLineNumbers();
            this.updateSymbolOverlay();
        }
    }
    
    getSelectedLines() {
        return Array.from(this.selectedLines);
    }
    
    clearSelection() {
        this.selectedLines.clear();
        if (this.editor) {
            this.updateLineHighlights();
        } else if (this.updateLineNumbers) {
            this.updateLineNumbers();
        }
    }
    
    focus() {
        if (this.editor) {
            this.editor.focus();
        } else if (this.textarea) {
            this.textarea.focus();
        }
    }
    
    dispose() {
        if (this.editor) {
            this.editor.dispose();
        }
    }
}

// 工具函数
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// 导出
window.AdvancedCodeEditor = AdvancedCodeEditor;