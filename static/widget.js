/**
 * Embeddable Looker Chatbot Widget
 * This script creates a floating chat widget that can be embedded on any website
 */

class LookerChatWidget {
    constructor(options = {}) {
        this.options = {
            apiBaseUrl: options.apiBaseUrl || window.location.origin,
            position: options.position || 'bottom-right',
            theme: options.theme || 'dark',
            ...options
        };
        
        this.isOpen = false;
        this.isMinimized = false;
        this.chatHistory = [];
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.createWidget();
        this.attachEventListeners();
        this.loadChatHistory();
    }
    
    createWidget() {
        // Create widget container
        this.widgetContainer = document.createElement('div');
        this.widgetContainer.id = 'looker-chat-widget';
        this.widgetContainer.className = 'looker-chat-widget';
        
        // Create floating button
        this.createFloatingButton();
        
        // Create chat window
        this.createChatWindow();
        
        // Add to page
        document.body.appendChild(this.widgetContainer);
    }
    
    createFloatingButton() {
        this.floatingButton = document.createElement('div');
        this.floatingButton.className = 'chat-floating-button';
        this.floatingButton.innerHTML = `
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
        `;
        this.widgetContainer.appendChild(this.floatingButton);
    }
    
    createChatWindow() {
        this.chatWindow = document.createElement('div');
        this.chatWindow.className = 'chat-window';
        this.chatWindow.style.display = 'none';
        
        this.chatWindow.innerHTML = `
            <div class="chat-header">
                <div class="chat-title">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 19c-5 0-8-3-8-8s3-8 8-8 8 3 8 8-3 8-8 8z"></path>
                        <path d="M21 12c0 4.418-3.582 8-8 8"></path>
                    </svg>
                    Data Analyst Assistant
                </div>
                <div class="chat-controls">
                    <button class="btn-minimize" title="Minimize">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </button>
                    <button class="btn-close" title="Close">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="welcome-message">
                    <div class="message assistant-message">
                        <div class="message-content">
                            👋 Hi! I'm your data analyst assistant. I can help you explore and analyze data from your Looker BI platform. 
                            <br><br>
                            Ask me questions like:
                            <ul>
                                <li>"What are our top performing products this quarter?"</li>
                                <li>"Show me sales trends by region"</li>
                                <li>"What's the customer acquisition cost?"</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div class="chat-input-container">
                <div class="input-group">
                    <input type="text" class="chat-input" placeholder="Ask me about your data..." maxlength="500">
                    <button class="btn-send" disabled>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22,2 15,22 11,13 2,9"></polygon>
                        </svg>
                    </button>
                </div>
                <div class="chat-footer">
                    <small>Powered by Looker BI • Press Enter to send</small>
                </div>
            </div>
        `;
        
        this.widgetContainer.appendChild(this.chatWindow);
    }
    
    attachEventListeners() {
        // Floating button click
        this.floatingButton.addEventListener('click', () => {
            this.toggleChat();
        });
        
        // Chat controls
        const minimizeBtn = this.chatWindow.querySelector('.btn-minimize');
        const closeBtn = this.chatWindow.querySelector('.btn-close');
        const sendBtn = this.chatWindow.querySelector('.btn-send');
        const chatInput = this.chatWindow.querySelector('.chat-input');
        
        minimizeBtn.addEventListener('click', () => {
            this.minimizeChat();
        });
        
        closeBtn.addEventListener('click', () => {
            this.closeChat();
        });
        
        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Input events
        chatInput.addEventListener('input', (e) => {
            sendBtn.disabled = !e.target.value.trim();
        });
        
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Prevent click propagation on chat window
        this.chatWindow.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        this.isOpen = true;
        this.isMinimized = false;
        this.chatWindow.style.display = 'flex';
        this.chatWindow.classList.add('chat-window-open');
        this.floatingButton.style.display = 'none';
        
        // Focus input
        setTimeout(() => {
            const input = this.chatWindow.querySelector('.chat-input');
            input.focus();
        }, 300);
    }
    
    closeChat() {
        this.isOpen = false;
        this.isMinimized = false;
        this.chatWindow.classList.remove('chat-window-open');
        
        setTimeout(() => {
            this.chatWindow.style.display = 'none';
            this.floatingButton.style.display = 'flex';
        }, 300);
    }
    
    minimizeChat() {
        this.isMinimized = true;
        this.chatWindow.classList.add('chat-window-minimized');
        
        setTimeout(() => {
            this.chatWindow.style.display = 'none';
            this.floatingButton.style.display = 'flex';
        }, 300);
    }
    
    async sendMessage() {
        const input = this.chatWindow.querySelector('.chat-input');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;
        
        // Add user message to chat
        this.addMessage(message, 'user');
        input.value = '';
        this.chatWindow.querySelector('.btn-send').disabled = true;
        
        // Show loading indicator
        this.showLoading();
        
        try {
            const response = await this.sendToAPI(message);
            this.hideLoading();
            
            if (response.error) {
                this.addMessage(response.error, 'assistant', 'error');
            } else {
                this.addMessage(response.response, 'assistant');
            }
        } catch (error) {
            this.hideLoading();
            console.error('Chat error:', error);
            this.addMessage('Sorry, I encountered an error. Please try again later.', 'assistant', 'error');
        }
        
        // Save chat history
        this.saveChatHistory();
    }
    
    async sendToAPI(message) {
        const response = await fetch(`${this.options.apiBaseUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    addMessage(content, sender, type = 'normal') {
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message ${type === 'error' ? 'error-message' : ''}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = this.formatMessage(content);
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(timestamp);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Store in history
        this.chatHistory.push({ content, sender, timestamp: Date.now(), type });
    }
    
    formatMessage(content) {
        // Basic formatting for better readability
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    showLoading() {
        this.isLoading = true;
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message loading-message';
        loadingDiv.id = 'loading-message';
        loadingDiv.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                Analyzing your data...
            </div>
        `;
        
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    hideLoading() {
        this.isLoading = false;
        const loadingMessage = this.chatWindow.querySelector('#loading-message');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }
    
    saveChatHistory() {
        try {
            sessionStorage.setItem('looker-chat-history', JSON.stringify(this.chatHistory));
        } catch (error) {
            console.warn('Failed to save chat history:', error);
        }
    }
    
    loadChatHistory() {
        try {
            const saved = sessionStorage.getItem('looker-chat-history');
            if (saved) {
                this.chatHistory = JSON.parse(saved);
                // Restore messages (except welcome message)
                const messagesContainer = this.chatWindow.querySelector('#chat-messages');
                const welcomeMessage = messagesContainer.querySelector('.welcome-message');
                
                this.chatHistory.forEach(msg => {
                    if (msg.sender !== 'welcome') {
                        this.addMessageToDOM(msg.content, msg.sender, msg.type);
                    }
                });
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
        }
    }
    
    addMessageToDOM(content, sender, type = 'normal') {
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message ${type === 'error' ? 'error-message' : ''}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = this.formatMessage(content);
        
        messageDiv.appendChild(messageContent);
        messagesContainer.appendChild(messageDiv);
    }
    
    // Public methods for external control
    clearHistory() {
        this.chatHistory = [];
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        const messages = messagesContainer.querySelectorAll('.message:not(.welcome-message .message)');
        messages.forEach(msg => msg.remove());
        this.saveChatHistory();
    }
}

// Auto-initialize if not loaded as module
if (typeof module === 'undefined') {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.lookerChatWidget = new LookerChatWidget();
        });
    } else {
        window.lookerChatWidget = new LookerChatWidget();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LookerChatWidget;
}
