document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const newChatBtn = document.getElementById('newChatBtn');
    const inputContainer = document.getElementById('inputContainer');

    let isProcessing = false;
    let currentAssistantMessage = null;

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        updateSendButton();
    });

    // Enable/disable send button based on input
    function updateSendButton() {
        const hasContent = messageInput.value.trim().length > 0;
        sendButton.disabled = !hasContent || isProcessing;
    }

    // Handle Enter key
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled) {
                sendMessage();
            }
        }
    });

    // Send button click
    sendButton.addEventListener('click', sendMessage);

    // New chat button
    newChatBtn.addEventListener('click', async function() {
        if (confirm('Start a new conversation? This will clear your current chat history.')) {
            try {
                const response = await fetch('/clear-history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });

                if (response.ok) {
                    // Add centered class back
                    inputContainer.classList.add('centered');
                    
                    // Clear messages and show welcome screen
                    chatMessages.innerHTML = `
                        <div class="welcome-section">
                            <div class="welcome-icon">
                                <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <rect width="64" height="64" rx="12" fill="url(#gradient2)"/>
                                    <path d="M20 35L28 27L36 35L44 23" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                                    <circle cx="44" cy="23" r="2" fill="white"/>
                                    <path d="M16 44H48" stroke="white" stroke-width="2" stroke-linecap="round"/>
                                    <defs>
                                        <linearGradient id="gradient2" x1="0" y1="0" x2="64" y2="64">
                                            <stop offset="0%" stop-color="#3b82f6"/>
                                            <stop offset="100%" stop-color="#1d4ed8"/>
                                        </linearGradient>
                                    </defs>
                                </svg>
                            </div>
                            <h2>Welcome to Investment Advisor</h2>
                            <p>Your AI-powered partner for intelligent stock market analysis and investment insights.</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error clearing history:', error);
            }
        }
    });

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message || isProcessing) return;

        isProcessing = true;
        sendButton.disabled = true;

        // Remove centered class from input container
        inputContainer.classList.remove('centered');

        // Hide welcome section if it exists
        const welcomeSection = chatMessages.querySelector('.welcome-section');
        if (welcomeSection) {
            welcomeSection.style.display = 'none';
        }

        // Change placeholder after first message
        messageInput.placeholder = 'Ask me anything about stock investment strategies to continue.';

        // Add user message
        addMessage('user', message);

        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Add typing indicator with "Processing..." text
        const typingIndicator = addTypingIndicator();

        try {
            const response = await fetch('/stream-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            // Remove typing indicator
            typingIndicator.remove();

            // Create assistant message container
            currentAssistantMessage = createAssistantMessage();
            const contentElement = currentAssistantMessage.querySelector('.message-content');

            // Read the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                accumulatedText += chunk;
                
                // Format and update content with accumulated text
                contentElement.innerHTML = formatMessageContent(accumulatedText);
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            currentAssistantMessage = null;

        } catch (error) {
            console.error('Error:', error);
            if (typingIndicator && typingIndicator.parentNode) {
                typingIndicator.remove();
            }
            addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        } finally {
            isProcessing = false;
            updateSendButton();
        }
    }

    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = role === 'user' 
            ? document.querySelector('.username').textContent.charAt(0).toUpperCase()
            : 'AI';
        
        const roleName = role === 'user' ? 'You' : 'Investment Advisor';
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">${avatar}</div>
                <div class="message-role">${roleName}</div>
            </div>
            <div class="message-content">${escapeHtml(content)}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }

    function createAssistantMessage() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">AI</div>
                <div class="message-role">Investment Advisor</div>
            </div>
            <div class="message-content"></div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }

    function addTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message assistant';
        
        indicatorDiv.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">AI</div>
                <div class="message-role">Investment Advisor</div>
            </div>
            <div class="processing-indicator">
                <div class="spinner"></div>
                <span class="processing-text">Processing...</span>
            </div>
        `;
        
        chatMessages.appendChild(indicatorDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return indicatorDiv;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatMessageContent(text) {
        // Escape HTML first
        let formatted = escapeHtml(text);
        
        // Replace numbered items like "1) " with proper formatting
        formatted = formatted.replace(/(\d+)\)\s+([^\n]+)/g, '<div class="numbered-item"><span class="number">$1.</span> $2</div>');
        
        // Replace section headers (text ending with colon followed by content)
        formatted = formatted.replace(/([A-Za-z &]+):\s+([^\n]+)/g, '<div class="section"><strong>$1:</strong> $2</div>');
        
        // Replace double line breaks with paragraph breaks
        formatted = formatted.replace(/\n\n/g, '</p><p>');
        
        // Replace single line breaks with <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Wrap in paragraph if not already wrapped
        if (!formatted.startsWith('<div') && !formatted.startsWith('<p>')) {
            formatted = '<p>' + formatted + '</p>';
        }
        
        return formatted;
    }

    // Initial focus on input
    messageInput.focus();
});
