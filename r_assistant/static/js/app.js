/**
 * R语言智能助手 - 主JavaScript文件
 * 包含通用功能和工具函数
 */

class RAssistantApp {
    constructor() {
        this.apiBaseUrl = '/api';
        this.loadingModal = null;
        this.toastContainer = null;
        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.init();
    }

    init() {
        this.setupParticles();
        this.setupModals();
        this.setupToasts();
        this.setupEventListeners();
        this.initPrism();
    }

    // 初始化粒子背景
    setupParticles() {
        if (this.prefersReducedMotion) {
            return;
        }

        if (typeof particlesJS !== 'undefined') {
            particlesJS('particles-js', {
                particles: {
                    number: {
                        value: 50,
                        density: {
                            enable: true,
                            value_area: 800
                        }
                    },
                    color: {
                        value: '#667eea'
                    },
                    shape: {
                        type: 'circle',
                        stroke: {
                            width: 0,
                            color: '#000000'
                        }
                    },
                    opacity: {
                        value: 0.3,
                        random: false,
                        anim: {
                            enable: false,
                            speed: 1,
                            opacity_min: 0.1,
                            sync: false
                        }
                    },
                    size: {
                        value: 3,
                        random: true,
                        anim: {
                            enable: false,
                            speed: 40,
                            size_min: 0.1,
                            sync: false
                        }
                    },
                    line_linked: {
                        enable: true,
                        distance: 150,
                        color: '#667eea',
                        opacity: 0.2,
                        width: 1
                    },
                    move: {
                        enable: true,
                        speed: 2,
                        direction: 'none',
                        random: false,
                        straight: false,
                        out_mode: 'out',
                        bounce: false,
                        attract: {
                            enable: false,
                            rotateX: 600,
                            rotateY: 1200
                        }
                    }
                },
                interactivity: {
                    detect_on: 'canvas',
                    events: {
                        onhover: {
                            enable: true,
                            mode: 'repulse'
                        },
                        onclick: {
                            enable: true,
                            mode: 'push'
                        },
                        resize: true
                    },
                    modes: {
                        grab: {
                            distance: 400,
                            line_linked: {
                                opacity: 1
                            }
                        },
                        bubble: {
                            distance: 400,
                            size: 40,
                            duration: 2,
                            opacity: 8,
                            speed: 3
                        },
                        repulse: {
                            distance: 100,
                            duration: 0.4
                        },
                        push: {
                            particles_nb: 4
                        },
                        remove: {
                            particles_nb: 2
                        }
                    }
                },
                retina_detect: true
            });
        }
    }

    // 设置模态框
    setupModals() {
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'), {
            backdrop: 'static',
            keyboard: false
        });
    }

    // 设置Toast通知
    setupToasts() {
        this.toastContainer = document.getElementById('toastContainer');
    }

    // 设置事件监听器
    setupEventListeners() {
        // CSRF Token设置
        this.setupCSRF();
        
        // 代码高亮
        document.addEventListener('DOMContentLoaded', () => {
            this.highlightCode();
        });

        // 复制代码功能
        this.setupCodeCopy();

        // 滚动效果
        this.setupScrollEffects();
    }

    // 初始化Prism代码高亮
    initPrism() {
        if (typeof Prism !== 'undefined') {
            Prism.highlightAll();
        }
    }

    // 设置CSRF令牌
    setupCSRF() {
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            // 为所有AJAX请求设置CSRF令牌
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!this.crossDomain && !settings.headers['X-CSRFToken']) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken);
                    }
                }
            });
        }
    }

    // 获取CSRF令牌
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }

    // 显示加载状态
    showLoading(message = 'AI正在思考中...') {
        const modalBody = document.querySelector('#loadingModal .modal-body p');
        if (modalBody) {
            modalBody.textContent = message;
        }
        this.loadingModal.show();
    }

    // 隐藏加载状态
    hideLoading() {
        this.loadingModal.hide();
    }

    // 显示Toast通知
    showToast(message, type = 'info', duration = 5000) {
        const toastId = 'toast_' + Date.now();
        const iconClass = {
            'success': 'fas fa-check-circle text-success',
            'error': 'fas fa-exclamation-circle text-danger',
            'warning': 'fas fa-exclamation-triangle text-warning',
            'info': 'fas fa-info-circle text-info'
        }[type] || 'fas fa-info-circle text-info';

        const toastHTML = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="${iconClass} me-2"></i>
                    <strong class="me-auto">系统通知</strong>
                    <small>刚刚</small>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        this.toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });
        
        toast.show();

        // 自动移除DOM元素
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // 高亮代码
    highlightCode() {
        if (typeof Prism !== 'undefined') {
            // 重新高亮所有代码块
            Prism.highlightAll();
            
            // 为新添加的代码块添加复制按钮
            this.addCopyButtons();
        }
    }

    // 设置代码复制功能
    setupCodeCopy() {
        this.addCopyButtons();
    }

    // 添加复制按钮到代码块
    addCopyButtons() {
        const codeBlocks = document.querySelectorAll('pre[class*="language-"]');
        
        codeBlocks.forEach(block => {
            // 避免重复添加按钮
            if (block.querySelector('.copy-button')) return;
            
            const button = document.createElement('button');
            button.className = 'copy-button btn btn-sm btn-outline-light position-absolute top-0 end-0 m-2';
            button.innerHTML = '<i class="fas fa-copy"></i>';
            button.title = '复制代码';
            
            button.addEventListener('click', () => {
                this.copyCodeToClipboard(block, button);
            });
            
            block.style.position = 'relative';
            block.appendChild(button);
        });
    }

    // 复制代码到剪贴板
    async copyCodeToClipboard(codeBlock, button) {
        const code = codeBlock.querySelector('code').textContent;
        
        try {
            await navigator.clipboard.writeText(code);
            
            // 更新按钮状态
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-check text-success"></i>';
            button.disabled = true;
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.disabled = false;
            }, 2000);
            
            this.showToast('代码已复制到剪贴板', 'success', 2000);
        } catch (err) {
            this.showToast('复制失败，请手动复制', 'error');
        }
    }

    // 设置滚动效果
    setupScrollEffects() {
        // 导航栏滚动效果
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (ticking) return;
            ticking = true;

            window.requestAnimationFrame(() => {
                const navbar = document.querySelector('.navbar');
                if (navbar) {
                    navbar.classList.toggle('scrolled', window.scrollY > 50);
                }
                ticking = false;
            });
        }, { passive: true });

        // 元素进入视图动画
        this.setupIntersectionObserver();
    }

    // 设置交叉观察器
    setupIntersectionObserver() {
        const animateElements = document.querySelectorAll('[data-reveal], .feature-card, .tech-card, .step-item, .stat-item, .demo-chat, .quickstart-section .step-item');

        if (animateElements.length === 0) {
            return;
        }

        document.body.classList.add('reveal-ready');

        animateElements.forEach(el => {
            if (!el.classList.contains('reveal')) {
                el.classList.add('reveal');
            }
        });

        if (!('IntersectionObserver' in window)) {
            animateElements.forEach(el => el.classList.add('is-visible'));
            return;
        }

        if (this.prefersReducedMotion) {
            animateElements.forEach(el => el.classList.add('is-visible'));
            return;
        }

        const observerOptions = {
            threshold: 0.15,
            rootMargin: '0px 0px -40px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        animateElements.forEach(el => observer.observe(el));

        // 确保初始视窗中的元素立即可见
        requestAnimationFrame(() => {
            animateElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.top < window.innerHeight && rect.bottom > 0) {
                    el.classList.add('is-visible');
                }
            });
        });
    }

    // API请求辅助方法
    async makeApiRequest(endpoint, data, method = 'POST') {
        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: method !== 'GET' ? JSON.stringify(data) : undefined
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // 格式化时间
    formatTime(seconds) {
        if (seconds < 1) {
            return `${Math.round(seconds * 1000)}ms`;
        }
        return `${seconds.toFixed(2)}s`;
    }

    // 格式化代码
    formatCode(code, language = 'r') {
        // 基本的代码格式化
        return code
            .replace(/\t/g, '  ') // 将tab替换为2个空格
            .replace(/^\s+|\s+$/g, '') // 去除首尾空格
            .split('\n')
            .map(line => line.trimEnd()) // 去除行尾空格
            .join('\n');
    }

    // 验证R代码
    validateRCode(code) {
        const errors = [];
        
        // 基本语法检查
        const lines = code.split('\n');
        let brackets = 0;
        let quotes = 0;
        
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line || line.startsWith('#')) continue;
            
            // 检查括号配对
            for (const char of line) {
                if (char === '(' || char === '[' || char === '{') brackets++;
                if (char === ')' || char === ']' || char === '}') brackets--;
                if (char === '"' || char === "'") quotes++;
            }
        }
        
        if (brackets !== 0) {
            errors.push('括号不匹配');
        }
        
        if (quotes % 2 !== 0) {
            errors.push('引号不匹配');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    // 生成唯一ID
    generateId() {
        return 'id_' + Math.random().toString(36).substr(2, 9);
    }

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
}

// 全局应用实例
window.RAssistant = new RAssistantApp();

// 工具函数
window.RAssistantUtils = {
    // 安全的HTML转义
    escapeHtml: function(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // 解析Markdown（使用marked.js）
    parseMarkdown: function(text) {
        if (typeof marked !== 'undefined') {
            // 配置marked选项
            marked.setOptions({
                highlight: function(code, lang) {
                    if (Prism.languages[lang]) {
                        return Prism.highlight(code, Prism.languages[lang], lang);
                    }
                    return code;
                },
                breaks: true,
                gfm: true
            });
            return marked.parse(text);
        } else {
            // 降级到简单实现
            return text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        }
    },

    // 下载文件
    downloadFile: function(content, filename, type = 'text/plain') {
        const blob = new Blob([content], { type: type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },

    // 格式化文件大小
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
};

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('R语言智能助手已加载');
    
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});