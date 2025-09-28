class ChatExperience {
    constructor(options = {}) {
        const {
            container,
            form,
            input,
            history = [],
            quickReplies = [],
            composerActions = [],
            statusBar,
            clearHistoryForm,
            endpoints = {}
        } = options;

        this.container = container;
        this.form = form;
        this.input = input;
        this.history = Array.isArray(history) ? history : [];
        this.quickReplies = quickReplies;
        this.composerActions = composerActions;
        this.statusBar = statusBar;
        this.clearHistoryForm = clearHistoryForm;
        this.endpoints = {
            talk: endpoints.talk || '/api/talk/',
            clearHistory: endpoints.clearHistory || '/api/history/clear/'
        };

        this.messageStore = [];
        this.typingTimer = null;
        this.hintTimer = null;
        this.sessionDraftKey = 'ra-chat-draft';
        this.isSending = false;
        this.typingIndicatorEl = null;
        this.sessionStart = new Date();
        this.scrollLock = false;
        this.defaultLatencyLabel = '--';
        this.hints = [
            '尝试补充数据上下文，AI 会自动结合历史对话。',
            '提及目标：例如“生成一份实验报告”，可获得结构化回答。',
            '可以拖入 R 脚本片段，AI 会智能记忆关键函数。',
            '想要延伸讨论？输入“继续”或点击任意回答下的追问按钮。'
        ];
    }

    init() {
        if (!this.container || !this.form || !this.input) {
            return;
        }

        this.restoreDraft();
        this.renderHistory();
        this.setupForm();
        this.setupQuickReplies();
        this.setupComposerActions();
        this.setupClearHistory();
        this.startHintRotation();
        this.observeScroll();
        this.updateSessionSummary();
    }

    renderHistory() {
        if (!this.history.length) {
            this.renderEmptyState();
            return;
        }

        const fragment = document.createDocumentFragment();
        this.history.forEach((item) => {
            const message = {
                role: item.role === 'assistant' ? 'assistant' : 'user',
                content: item.content || '',
                timestamp: item.timestamp ? new Date(item.timestamp) : null,
                status: 'delivered'
            };
            const element = this.createMessageElement(message);
            fragment.appendChild(element);
            this.messageStore.push(message);
        });

        this.container.appendChild(fragment);
        this.scrollToBottom(true);
    }

    renderEmptyState() {
        const empty = document.createElement('div');
        empty.className = 'empty-state py-4 text-center';
        empty.innerHTML = '<i class="fas fa-comment-dots fa-2x mb-3"></i><p class="mb-0">开始您的第一次对话吧！</p>';
        this.container.appendChild(empty);
    }

    setupForm() {
        this.form.addEventListener('submit', (event) => {
            event.preventDefault();
            this.sendCurrentMessage();
        });

        this.input.addEventListener('keydown', (event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                event.preventDefault();
                this.sendCurrentMessage();
                return;
            }

            if (event.shiftKey && event.key === 'Enter') {
                // allow newline
                return;
            }

            if (event.key === 'Escape') {
                this.clearComposer();
            }
        });

        this.input.addEventListener('input', () => {
            this.autoResizeInput();
            this.saveDraft();
        });

        this.autoResizeInput();
    }

    setupQuickReplies() {
        if (!this.quickReplies?.length) return;

        this.quickReplies.forEach((button) => {
            button.addEventListener('click', () => {
                const value = button.dataset.quickReply || '';
                this.setComposerValue(value);
            });
        });
    }

    setupComposerActions() {
        if (!this.composerActions?.length) return;

        this.composerActions.forEach((button) => {
            button.addEventListener('click', () => {
                const action = button.dataset.composerAction;
                switch (action) {
                    case 'clear':
                        this.clearComposer();
                        break;
                    case 'code':
                        this.insertCodeFence();
                        break;
                    case 'remember':
                        this.toggleDraftStorage(button);
                        break;
                }
            });
        });
    }

    setupClearHistory() {
        if (!this.clearHistoryForm) return;

        this.clearHistoryForm.addEventListener('submit', (event) => {
            event.preventDefault();
            this.clearConversation();
        });
    }

    startHintRotation() {
        const hintTarget = document.querySelector('[data-dynamic-hint]');
        if (!hintTarget) return;

        let index = 0;
        const updateHint = () => {
            hintTarget.innerHTML = `<span><i class="fas fa-wand-magic-sparkles"></i>${this.hints[index]}</span>`;
            index = (index + 1) % this.hints.length;
        };

        updateHint();
        this.hintTimer = window.setInterval(updateHint, 8000);
    }

    observeScroll() {
        this.container.addEventListener('scroll', () => {
            const distanceFromBottom = this.container.scrollHeight - this.container.clientHeight - this.container.scrollTop;
            this.scrollLock = distanceFromBottom > 120;
        }, { passive: true });
    }

    sendCurrentMessage() {
        const raw = (this.input.value || '').trim();
        if (!raw || this.isSending) {
            return;
        }

        this.isSending = true;
        const message = {
            role: 'user',
            content: raw,
            timestamp: new Date(),
            status: 'sending'
        };

        const element = this.createMessageElement(message);
        this.container.appendChild(element);
        this.messageStore.push(message);
    this.updateSessionSummary();
        this.scrollToBottom();

        this.clearComposer();

        const typingEl = this.showTypingIndicator();
        const startedAt = performance.now();

        const csrfToken = this.getCSRFToken();

        fetch(this.endpoints.talk, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ message: raw })
        })
            .then(async (response) => {
                if (!response.ok) {
                    const error = await response.json().catch(() => ({ error: '服务暂不可用' }));
                    throw new Error(error.error || '发送失败');
                }
                return response.json();
            })
            .then((data) => {
                const latency = performance.now() - startedAt;
                this.applyLatency(latency);
                message.status = 'delivered';
                this.updateMessageStatus(element, 'delivered');

                const assistantMessage = {
                    role: 'assistant',
                    content: data.response || '',
                    timestamp: new Date(),
                    status: 'delivered'
                };

                const assistantEl = this.replaceTypingIndicator(typingEl, assistantMessage);
                this.messageStore.push(assistantMessage);
                this.updateSessionSummary();
                this.scrollToBottom();
            })
            .catch((error) => {
                message.status = 'failed';
                this.updateMessageStatus(element, 'failed', error.message);
                this.removeTypingIndicator(typingEl);
                this.isSending = false;
                this.updateSessionSummary();
                window.RAssistant?.showToast?.(error.message || '发送失败，请稍后再试', 'error');
            })
            .finally(() => {
                this.isSending = false;
            });
    }

    showTypingIndicator() {
        const indicatorMessage = {
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            status: 'typing'
        };

        const element = this.createMessageElement(indicatorMessage);
        this.container.appendChild(element);
        this.typingIndicatorEl = element;
        this.scrollToBottom();
        return element;
    }

    replaceTypingIndicator(indicator, message) {
        if (!indicator) return this.createMessageElement(message);

        const replacement = this.createMessageElement(message);
        indicator.replaceWith(replacement);
        this.typingIndicatorEl = null;
        return replacement;
    }

    removeTypingIndicator(indicator) {
        if (indicator && indicator.parentElement) {
            indicator.parentElement.removeChild(indicator);
        }
        this.typingIndicatorEl = null;
    }

    createMessageElement(message) {
        const { role, content, timestamp, status } = message;
        const wrapper = document.createElement('article');
        wrapper.className = `chat-message ${role}`;

        const layout = document.createElement('div');
        layout.className = 'd-flex align-items-start gap-3';

        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}`;
        avatar.innerHTML = role === 'user'
            ? '<i class="fas fa-user-astronaut"></i>'
            : '<i class="fas fa-robot"></i>';

        const body = document.createElement('div');
        body.className = 'message-body flex-grow-1';

        const meta = document.createElement('div');
        meta.className = 'message-meta d-flex align-items-center gap-2 mb-2';
        const label = role === 'user' ? '您' : 'AI助手';
        const timeLabel = timestamp ? this.formatTime(timestamp) : '';
        const statusLabel = this.renderStatusBadge(status);
        meta.innerHTML = `<strong>${label}</strong>${timeLabel ? `<time datetime="${timestamp.toISOString()}"><i class="fas fa-clock"></i>${timeLabel}</time>` : ''}${statusLabel}`;

        const contentContainer = document.createElement('div');
        contentContainer.className = 'message-content markdown-content';

        if (status === 'typing') {
            contentContainer.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        } else if (role === 'assistant') {
            contentContainer.innerHTML = this.renderMarkdown(content);
        } else {
            contentContainer.textContent = content;
        }

        const actions = this.createMessageActions(message);

        body.appendChild(meta);
        body.appendChild(contentContainer);
        if (actions) {
            body.appendChild(actions);
        }

        layout.appendChild(avatar);
        layout.appendChild(body);
        wrapper.appendChild(layout);

        window.requestAnimationFrame(() => wrapper.classList.add('is-visible'));
        return wrapper;
    }

    renderMarkdown(text) {
        if (!text) return '';

        let html = text;
        if (window.marked) {
            html = window.marked.parse(text, { breaks: true });
        } else {
            html = text.replace(/\n/g, '<br>');
        }

        if (window.DOMPurify) {
            html = window.DOMPurify.sanitize(html);
        }

        return html;
    }

    createMessageActions(message) {
        const buttons = [];
        buttons.push({ action: 'copy', label: '复制', icon: 'fas fa-copy' });

        if (message.role === 'assistant') {
            buttons.push({ action: 'follow-up', label: '追问建议', icon: 'fas fa-wand-magic-sparkles' });
        } else {
            buttons.push({ action: 'resend', label: '再次发送', icon: 'fas fa-paper-plane-top' });
        }

        if (!buttons.length) return null;

        const wrapper = document.createElement('div');
        wrapper.className = 'message-actions';

        buttons.forEach((btn) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.dataset.action = btn.action;
            button.className = 'btn btn-sm';
            button.innerHTML = `<i class="${btn.icon}"></i>${btn.label}`;
            button.addEventListener('click', () => this.handleMessageAction(btn.action, message));
            wrapper.appendChild(button);
        });

        return wrapper;
    }

    handleMessageAction(action, message) {
        switch (action) {
            case 'copy':
                this.copyToClipboard(message.content);
                break;
            case 'follow-up':
                this.setComposerValue(this.buildFollowUpPrompt(message.content));
                window.RAssistant?.showToast?.('已为您生成追问草稿', 'info');
                break;
            case 'resend':
                if (!this.isSending) {
                    this.setComposerValue(message.content);
                    this.sendCurrentMessage();
                }
                break;
            default:
                break;
        }
    }

    buildFollowUpPrompt(content = '') {
        if (!content.trim()) {
            return '请继续深入扩展刚才的回答。';
        }

        const preview = content.replace(/\s+/g, ' ').slice(0, 60);
        return `基于你之前的回答“${preview}…”，请继续给出更深入的分析和下一步建议。`;
    }

    updateMessageStatus(element, status, errorMessage = '') {
        if (!element) return;
        const badge = element.querySelector('[data-message-status]');
        if (!badge) return;

        switch (status) {
            case 'delivered':
                badge.textContent = '已送达';
                badge.className = 'badge rounded-pill bg-success-subtle text-success';
                break;
            case 'failed':
                badge.textContent = '发送失败';
                badge.className = 'badge rounded-pill bg-danger-subtle text-danger';
                if (errorMessage) {
                    badge.title = errorMessage;
                }
                break;
            case 'sending':
            default:
                badge.textContent = '发送中';
                badge.className = 'badge rounded-pill bg-secondary-subtle text-secondary';
        }
    }

    renderStatusBadge(status = 'delivered') {
        const labelMap = {
            sending: { text: '发送中', cls: 'bg-secondary-subtle text-secondary' },
            delivered: { text: '已送达', cls: 'bg-success-subtle text-success' },
            failed: { text: '发送失败', cls: 'bg-danger-subtle text-danger' },
            typing: { text: '生成中', cls: 'bg-info-subtle text-info' }
        };

        const { text, cls } = labelMap[status] || labelMap.delivered;
        return `<span class="badge rounded-pill ${cls}" data-message-status>${text}</span>`;
    }

    updateSessionSummary() {
        const messageCount = this.messageStore.length;
        const lastMessage = this.messageStore[messageCount - 1];
        const timestamp = lastMessage?.timestamp instanceof Date ? lastMessage.timestamp : this.sessionStart;
        const relativeLabel = this.relativeTime(timestamp);

        document.querySelectorAll('[data-session-count]').forEach((el) => {
            el.textContent = messageCount.toString();
        });

        document.querySelectorAll('[data-session-last]').forEach((el) => {
            el.textContent = relativeLabel;
        });
    }

    clearConversation() {
        if (!confirm('确定要清除对话历史吗？')) {
            return;
        }

        const csrfToken = this.getCSRFToken();
        fetch(this.endpoints.clearHistory, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({})
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error('清除失败');
                }
                return response.json();
            })
            .then(() => {
                this.container.innerHTML = '';
                this.messageStore = [];
                this.renderEmptyState();
                this.updateSessionSummary();
                this.applyLatency(this.defaultLatencyLabel);
                window.RAssistant?.showToast?.('对话历史已清除', 'success');
            })
            .catch((error) => {
                window.RAssistant?.showToast?.(error.message || '清除失败，请稍后再试', 'error');
            });
    }

    clearComposer() {
        this.input.value = '';
        this.autoResizeInput();
        this.saveDraft('');
    }

    setComposerValue(value) {
        this.input.value = value;
        this.autoResizeInput();
        this.input.focus({ preventScroll: false });
    }

    insertCodeFence() {
        const selectionStart = this.input.selectionStart || 0;
        const selectionEnd = this.input.selectionEnd || 0;
        const value = this.input.value;
        const selectedText = value.slice(selectionStart, selectionEnd);
        const codeBlock = `\n\n\u0060\u0060\u0060r\n${selectedText || '# 在此粘贴R代码'}\n\u0060\u0060\u0060\n`;
        const updated = `${value.slice(0, selectionStart)}${codeBlock}${value.slice(selectionEnd)}`;
        this.setComposerValue(updated);

        const cursorPos = selectionStart + codeBlock.length;
        this.input.setSelectionRange(cursorPos, cursorPos);
    }

    toggleDraftStorage(button) {
        const currentValue = (this.input.value || '').trim();
        const stored = window.localStorage.getItem(this.sessionDraftKey);

        if (currentValue) {
            window.localStorage.setItem(this.sessionDraftKey, currentValue);
            button.classList.add('active');
            window.RAssistant?.showToast?.('草稿已暂存，可随时恢复', 'success');
        } else if (stored) {
            this.setComposerValue(stored);
            window.RAssistant?.showToast?.('已恢复上次草稿', 'info');
        } else {
            window.RAssistant?.showToast?.('暂无草稿内容', 'warning');
        }
    }

    restoreDraft() {
        const stored = window.localStorage.getItem(this.sessionDraftKey);
        if (stored && !this.input.value) {
            this.input.value = stored;
            this.autoResizeInput();
        }
    }

    saveDraft(value) {
        const content = typeof value === 'string' ? value : this.input.value;
        if (content) {
            window.localStorage.setItem(this.sessionDraftKey, content);
        } else {
            window.localStorage.removeItem(this.sessionDraftKey);
        }
    }

    autoResizeInput() {
        if (!this.input) return;
        this.input.style.height = 'auto';
        const maxHeight = parseInt(this.input.dataset.maxHeight || '240', 10);
        const nextHeight = Math.min(this.input.scrollHeight, maxHeight);
        this.input.style.height = `${nextHeight}px`;
    }

    scrollToBottom(force = false) {
        if (!force && this.scrollLock) {
            return;
        }
        this.container.scrollTo({
            top: this.container.scrollHeight,
            behavior: 'smooth'
        });
    }

    copyToClipboard(text = '') {
        if (!text) return;
        navigator.clipboard.writeText(text)
            .then(() => window.RAssistant?.showToast?.('已复制到剪贴板', 'success'))
            .catch(() => window.RAssistant?.showToast?.('复制失败，请手动复制', 'error'));
    }

    formatTime(date) {
        if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
            return '';
        }
        return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }

    relativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const minute = 60 * 1000;
        const hour = 60 * minute;

        if (diff < minute) return '刚刚';
        if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`;
        if (diff < 24 * hour) return `${Math.floor(diff / hour)} 小时前`;
        return date.toLocaleDateString('zh-CN');
    }

    getCSRFToken() {
        const tokenField = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return tokenField ? tokenField.value : '';
    }

    applyLatency(value) {
        const targets = document.querySelectorAll('[data-session-latency]');
        if (!targets.length) return;

        let label = '';
        if (typeof value === 'string') {
            label = value;
        } else {
            const seconds = value / 1000;
            if (Number.isNaN(seconds)) {
                label = this.defaultLatencyLabel;
            } else {
                label = seconds < 1 ? `${Math.round(value)} ms` : `${seconds.toFixed(1)} s`;
            }
        }

        targets.forEach((el) => {
            el.textContent = label;
        });
    }
}

window.ChatExperience = ChatExperience;
