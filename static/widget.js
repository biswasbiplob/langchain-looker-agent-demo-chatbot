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
        // Don't load chat history - we want fresh sessions each time
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
                    <button class="btn-logout" title="Logout">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                            <polyline points="16,17 21,12 16,7"></polyline>
                            <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                    </button>
                    <button class="btn-settings" title="Configuration Settings">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
                    </button>
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
            <div class="settings-panel" id="settings-panel" style="display: none;">
                <div class="settings-header">
                    <h3>Looker Configuration</h3>
                    <button class="btn-close-settings" title="Close Settings">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="settings-content">
                    <form class="settings-form">
                        <div class="form-group">
                            <label for="looker-base-url">Looker Base URL</label>
                            <input type="url" id="looker-base-url" placeholder="https://your-company.looker.com" />
                        </div>
                        <div class="form-group">
                            <label for="looker-client-id">Client ID</label>
                            <input type="text" id="looker-client-id" placeholder="Your Looker API client ID" />
                        </div>
                        <div class="form-group">
                            <label for="looker-client-secret">Client Secret</label>
                            <input type="password" id="looker-client-secret" placeholder="Your Looker API client secret" />
                        </div>
                        <div class="form-group">
                            <label for="openai-api-key">OpenAI API Key</label>
                            <input type="password" id="openai-api-key" placeholder="Your OpenAI API key" />
                        </div>
                        <div class="form-group">
                            <label for="lookml-model-name">LookML Model Name</label>
                            <input type="text" id="lookml-model-name" placeholder="Your LookML model name" />
                        </div>
                        <div class="settings-actions">
                            <button type="button" class="btn-save-settings">Save Configuration</button>
                            <button type="button" class="btn-test-connection">Test Connection</button>
                        </div>
                    </form>
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
        const settingsBtn = this.chatWindow.querySelector('.btn-settings');
        const minimizeBtn = this.chatWindow.querySelector('.btn-minimize');
        const closeBtn = this.chatWindow.querySelector('.btn-close');
        const sendBtn = this.chatWindow.querySelector('.btn-send');
        const chatInput = this.chatWindow.querySelector('.chat-input');
        
        settingsBtn.addEventListener('click', () => {
            this.openSettings();
        });
        
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
        
        // Settings panel controls
        const closeSettingsBtn = this.chatWindow.querySelector('.btn-close-settings');
        const saveSettingsBtn = this.chatWindow.querySelector('.btn-save-settings');
        const testConnectionBtn = this.chatWindow.querySelector('.btn-test-connection');
        
        closeSettingsBtn.addEventListener('click', () => {
            this.closeSettings();
        });
        
        saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });
        
        testConnectionBtn.addEventListener('click', () => {
            this.testConnection();
        });
        
        // Prevent click propagation on chat window
        this.chatWindow.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        
        // Load saved settings on init
        this.loadSettings();
        
        // Don't load chat history - we want fresh sessions each time
    }
    
    toggleChat() {
        if (this.isOpen && !this.isMinimized) {
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
        
        // Clear previous session and start fresh
        this.clearCurrentSession();
        
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
        
        // Clear the session on close
        this.clearServerSession();
        
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
            } else if (response.response) {
                this.addMessage(response.response, 'assistant');
            } else {
                console.error('Unexpected response format:', response);
                this.addMessage('I received an unexpected response format. Please try again.', 'assistant', 'error');
            }
        } catch (error) {
            this.hideLoading();
            console.error('Chat error:', error);
            
            // Try to get more detailed error information
            if (error.response) {
                try {
                    const errorData = await error.response.json();
                    this.addMessage(errorData.error || 'Sorry, I encountered an error. Please try again later.', 'assistant', 'error');
                } catch (parseError) {
                    this.addMessage('Sorry, I encountered an error. Please try again later.', 'assistant', 'error');
                }
            } else {
                this.addMessage('Sorry, I encountered an error. Please try again later.', 'assistant', 'error');
            }
        }
        
        // Save chat history
        this.saveChatHistory();
    }
    
    async sendToAPI(message) {
        try {
            // Get locally stored settings for widget usage
            const localSettings = this.getLocalSettings();
            
            const requestBody = { 
                message,
                settings: localSettings
            };
            
            const response = await fetch(`${this.options.apiBaseUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('Chatbot API not found. Please check that the apiBaseUrl is correct and points to your chatbot server.');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Unable to connect to chatbot server. Please check your internet connection and that the API URL is correct.');
            }
            throw error;
        }
    }
    
    getLocalSettings() {
        try {
            const saved = localStorage.getItem('looker-chat-settings');
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.warn('Failed to get local settings:', error);
            return {};
        }
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
    
    // Settings management methods
    openSettings() {
        const settingsPanel = this.chatWindow.querySelector('#settings-panel');
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        const inputContainer = this.chatWindow.querySelector('.chat-input-container');
        
        messagesContainer.style.display = 'none';
        inputContainer.style.display = 'none';
        settingsPanel.style.display = 'block';
    }
    
    closeSettings() {
        const settingsPanel = this.chatWindow.querySelector('#settings-panel');
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        const inputContainer = this.chatWindow.querySelector('.chat-input-container');
        
        settingsPanel.style.display = 'none';
        messagesContainer.style.display = 'flex';
        inputContainer.style.display = 'block';
    }
    
    async loadSettings() {
        try {
            // Load settings from server first
            const response = await fetch(`${this.options.apiBaseUrl}/api/get-settings`, {
                method: 'GET',
                credentials: 'include'
            });
            
            let settings = {};
            if (response.ok) {
                settings = await response.json();
            } else {
                // Fallback to local storage if server request fails
                const saved = localStorage.getItem('looker-chat-settings');
                if (saved) {
                    settings = JSON.parse(saved);
                }
            }
            
            const baseUrlInput = this.chatWindow.querySelector('#looker-base-url');
            const clientIdInput = this.chatWindow.querySelector('#looker-client-id');
            const clientSecretInput = this.chatWindow.querySelector('#looker-client-secret');
            const openaiKeyInput = this.chatWindow.querySelector('#openai-api-key');
            const modelNameInput = this.chatWindow.querySelector('#lookml-model-name');
            
            if (baseUrlInput) baseUrlInput.value = settings.lookerBaseUrl || '';
            if (clientIdInput) clientIdInput.value = settings.lookerClientId || '';
            if (clientSecretInput && settings.lookerClientSecret !== '***') {
                clientSecretInput.value = settings.lookerClientSecret || '';
            }
            if (openaiKeyInput && settings.openaiApiKey !== '***') {
                openaiKeyInput.value = settings.openaiApiKey || '';
            }
            if (modelNameInput) modelNameInput.value = settings.lookmlModelName || '';
            
        } catch (error) {
            console.warn('Failed to load settings:', error);
        }
    }
    
    async saveSettings() {
        const baseUrlInput = this.chatWindow.querySelector('#looker-base-url');
        const clientIdInput = this.chatWindow.querySelector('#looker-client-id');
        const clientSecretInput = this.chatWindow.querySelector('#looker-client-secret');
        const openaiKeyInput = this.chatWindow.querySelector('#openai-api-key');
        const modelNameInput = this.chatWindow.querySelector('#lookml-model-name');
        
        const settings = {
            lookerBaseUrl: baseUrlInput.value.trim(),
            lookerClientId: clientIdInput.value.trim(),
            lookerClientSecret: clientSecretInput.value.trim(),
            openaiApiKey: openaiKeyInput.value.trim(),
            lookmlModelName: modelNameInput.value.trim()
        };
        
        try {
            // Save to local storage
            localStorage.setItem('looker-chat-settings', JSON.stringify(settings));
            
            // Try to send to server to update configuration
            try {
                const response = await fetch(`${this.options.apiBaseUrl}/api/settings`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                    body: JSON.stringify(settings)
                });
                
                if (response.ok) {
                    this.addMessage('Configuration saved successfully! You can now start asking data questions.', 'assistant');
                    this.closeSettings();
                } else if (response.status === 404) {
                    this.addMessage('Configuration saved locally only. Server settings endpoint not available.', 'assistant');
                    this.closeSettings();
                } else {
                    throw new Error('Failed to save configuration to server');
                }
            } catch (serverError) {
                console.warn('Server save failed, using local storage only:', serverError);
                this.addMessage('Configuration saved locally. You can now start asking data questions.', 'assistant');
                this.closeSettings();
            }
        } catch (error) {
            console.error('Settings save error:', error);
            this.addMessage('Failed to save configuration. Please try again.', 'assistant', 'error');
        }
    }
    
    async testConnection() {
        try {
            const testBtn = this.chatWindow.querySelector('.btn-test-connection');
            testBtn.disabled = true;
            testBtn.textContent = 'Testing...';
            
            // Get locally stored settings for widget usage
            const localSettings = this.getLocalSettings();
            
            const response = await fetch(`${this.options.apiBaseUrl}/api/test-connection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ settings: localSettings })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.addMessage('Connection test successful! Your Looker configuration is working.', 'assistant');
            } else {
                this.addMessage(`Connection test failed: ${result.error}`, 'assistant', 'error');
            }
        } catch (error) {
            console.error('Connection test error:', error);
            this.addMessage('Failed to test connection. Please check your configuration.', 'assistant', 'error');
        } finally {
            const testBtn = this.chatWindow.querySelector('.btn-test-connection');
            testBtn.disabled = false;
            testBtn.textContent = 'Test Connection';
        }
    }

    // Session management methods
    clearCurrentSession() {
        // Clear local chat history
        this.chatHistory = [];
        
        // Clear messages from DOM (except welcome message)
        const messagesContainer = this.chatWindow.querySelector('#chat-messages');
        const messages = messagesContainer.querySelectorAll('.message:not(.welcome-message .message)');
        messages.forEach(msg => msg.remove());
        
        // Don't save to session storage - we want fresh sessions
    }
    
    async clearServerSession() {
        // Clear server-side session
        try {
            await fetch(`${this.options.apiBaseUrl}/api/chat/clear`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });
        } catch (error) {
            console.warn('Failed to clear server session:', error);
        }
    }

    // Public methods for external control
    clearHistory() {
        this.clearCurrentSession();
        this.clearServerSession();
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
