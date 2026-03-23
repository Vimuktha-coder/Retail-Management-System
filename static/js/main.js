// Core UI Interactions

document.addEventListener('DOMContentLoaded', () => {
    // Chat Widget Toggle
    const chatWidget = document.getElementById('chatWidget');
    const toggleChat = document.getElementById('toggleChat');
    const chatHeader = document.getElementById('chatHeader');

    if (chatHeader) {
        chatHeader.addEventListener('click', () => {
            if (chatWidget.classList.contains('closed')) {
                chatWidget.classList.remove('closed');
                chatWidget.classList.add('open');
                toggleChat.innerText = 'v';
            } else {
                chatWidget.classList.remove('open');
                chatWidget.classList.add('closed');
                toggleChat.innerText = '^';
            }
        });
    }

    // Chat API Request
    const sendChatBtn = document.getElementById('sendChat');
    const chatInput = document.getElementById('chatInput');
    const messages = document.getElementById('chatMessages');

    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', async () => {
            const text = chatInput.value.trim();
            if (text) {
                // Append user message
                const userMsg = document.createElement('div');
                userMsg.className = 'message user';
                userMsg.innerText = text;
                messages.appendChild(userMsg);
                chatInput.value = '';
                messages.scrollTop = messages.scrollHeight;

                // Add typing indicator
                const aiTyping = document.createElement('div');
                aiTyping.className = 'message ai text-muted';
                aiTyping.innerText = 'Thinking...';
                messages.appendChild(aiTyping);
                messages.scrollTop = messages.scrollHeight;

                try {
                    const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
                    const res = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'X-CSRFToken': token
                        },
                        body: JSON.stringify({ message: text })
                    });
                    
                    const result = await res.json();
                    
                    // Remove typing
                    messages.removeChild(aiTyping);
                    
                    // Add AI response
                    const aiMsg = document.createElement('div');
                    aiMsg.className = 'message ai';
                    aiMsg.innerText = result.response || result.error || 'Server Error';
                    messages.appendChild(aiMsg);
                    messages.scrollTop = messages.scrollHeight;
                } catch(e) {
                    messages.removeChild(aiTyping);
                    const aiMsg = document.createElement('div');
                    aiMsg.className = 'message ai';
                    aiMsg.innerText = 'Error connecting to chatbot.';
                    messages.appendChild(aiMsg);
                }
            }
        });
        
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') { sendChatBtn.click(); }
        });
    }
});
