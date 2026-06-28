(function() {
    // 1. Inject Styles
    const style = document.createElement('style');
    style.innerHTML = `
        #flowagent-widget-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 100000;
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .flowagent-bubble {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #00f2fe 0%, #4f46e5 100%);
            box-shadow: 0 4px 20px rgba(0, 242, 254, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .flowagent-bubble:hover {
            transform: scale(1.1) rotate(5deg);
        }
        .flowagent-bubble svg {
            width: 28px;
            height: 28px;
            fill: #ffffff;
        }
        .flowagent-chat-window {
            position: absolute;
            bottom: 80px;
            right: 0;
            width: 360px;
            height: 500px;
            background: rgba(10, 15, 30, 0.95);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: none;
            flex-direction: column;
            overflow: hidden;
            transition: all 0.3s ease;
            color: #cbd5e1;
        }
        .flowagent-chat-window.active {
            display: flex;
        }
        .flowagent-header {
            padding: 16px;
            background: linear-gradient(135deg, rgba(0, 242, 254, 0.1) 0%, rgba(79, 70, 229, 0.1) 100%);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .flowagent-header-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: #00f2fe;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .flowagent-header-close {
            cursor: pointer;
            color: #a0aec0;
            font-size: 1.2rem;
            transition: color 0.2s;
        }
        .flowagent-header-close:hover {
            color: #ffffff;
        }
        .flowagent-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .flowagent-msg {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        .flowagent-msg-user {
            background: #4f46e5;
            color: #ffffff;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .flowagent-msg-agent {
            background: rgba(255, 255, 255, 0.05);
            color: #e2e8f0;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid rgba(255, 255, 255, 0.03);
        }
        .flowagent-msg-system {
            font-size: 0.75rem;
            color: #718096;
            align-self: center;
            background: none;
            padding: 0;
        }
        .flowagent-input-area {
            padding: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            gap: 8px;
            background: rgba(10, 15, 30, 0.5);
        }
        .flowagent-input {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 10px;
            color: #ffffff;
            font-size: 0.85rem;
            outline: none;
        }
        .flowagent-input:focus {
            border-color: #00f2fe;
        }
        .flowagent-send-btn {
            background: #00f2fe;
            border: none;
            border-radius: 8px;
            width: 38px;
            height: 38px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: opacity 0.2s;
        }
        .flowagent-send-btn:hover {
            opacity: 0.9;
        }
        .flowagent-send-btn svg {
            width: 18px;
            height: 18px;
            fill: #0a0f1e;
        }
        .flowagent-typing-indicator {
            align-self: flex-start;
            display: none;
            background: rgba(255, 255, 255, 0.05);
            padding: 10px 14px;
            border-radius: 12px;
            border-bottom-left-radius: 4px;
            align-items: center;
            gap: 4px;
        }
        .flowagent-typing-dot {
            width: 6px;
            height: 6px;
            background: #a0aec0;
            border-radius: 50%;
            animation: flowagent-typing 1.4s infinite;
        }
        .flowagent-typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .flowagent-typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes flowagent-typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }
    `;
    document.head.appendChild(style);

    // 2. Render HTML structure
    const container = document.createElement('div');
    container.id = 'flowagent-widget-container';
    container.innerHTML = `
        <div class="flowagent-bubble" id="flowagent-bubble-trigger">
            <svg viewBox="0 0 24 24">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2m0 14H6l-2 2V4h16v12z"/>
            </svg>
        </div>
        <div class="flowagent-chat-window" id="flowagent-chat-window">
            <div class="flowagent-header">
                <div class="flowagent-header-title">
                    <span>🤖</span> FlowAgent AI Assistant
                </div>
                <div class="flowagent-header-close" id="flowagent-close-btn">&times;</div>
            </div>
            <div class="flowagent-messages" id="flowagent-messages-container">
                <div class="flowagent-msg flowagent-msg-agent">Hi there! How can I help you today? I can answer questions, handle inquiries or book demos in English, Hindi, or Hinglish.</div>
            </div>
            <div class="flowagent-typing-indicator" id="flowagent-typing">
                <div class="flowagent-typing-dot"></div>
                <div class="flowagent-typing-dot"></div>
                <div class="flowagent-typing-dot"></div>
            </div>
            <div class="flowagent-input-area">
                <input type="text" class="flowagent-input" id="flowagent-text-input" placeholder="Type a message..." autocomplete="off">
                <button class="flowagent-send-btn" id="flowagent-send-btn">
                    <svg viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(container);

    // 3. Script Logic
    const bubble = document.getElementById('flowagent-bubble-trigger');
    const windowEl = document.getElementById('flowagent-chat-window');
    const closeBtn = document.getElementById('flowagent-close-btn');
    const textInput = document.getElementById('flowagent-text-input');
    const sendBtn = document.getElementById('flowagent-send-btn');
    const messagesContainer = document.getElementById('flowagent-messages-container');
    const typingIndicator = document.getElementById('flowagent-typing');

    const sessionId = 'widget_' + Math.random().toString(36).substr(2, 9);
    const API_URL = 'http://localhost:8000'; // Target FastAPI Backend

    bubble.addEventListener('click', () => {
        windowEl.classList.toggle('active');
    });

    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        windowEl.classList.remove('active');
    });

    async function sendMessage() {
        const text = textInput.value.trim();
        if (!text) return;

        // Add user message to UI
        appendMessage(text, 'user');
        textInput.value = '';

        // Show typing indicator
        typingIndicator.style.display = 'flex';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch(`${API_URL}/api/widget/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text
                })
            });

            const data = await response.json();
            typingIndicator.style.display = 'none';

            if (data && data.final_answer) {
                appendMessage(data.final_answer, 'agent');
            } else {
                appendMessage("Sorry, I received an invalid response.", 'agent');
            }
        } catch (error) {
            typingIndicator.style.display = 'none';
            appendMessage("Unable to connect to FlowAgent server. Please try again later.", 'agent');
        }
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function appendMessage(text, sender) {
        const msg = document.createElement('div');
        msg.className = `flowagent-msg flowagent-msg-${sender}`;
        msg.textContent = text;
        messagesContainer.insertBefore(msg, typingIndicator);
    }

    sendBtn.addEventListener('click', sendMessage);
    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
})();
