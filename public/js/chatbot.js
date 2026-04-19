const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');

// -- BOOT ---------------------------------------------------------------
// Wait for auth to resolve so we know who the user is before greeting them
function _initChatbot() {
    const isLoggedIn = window._isLoggedIn;
    const profile = window._userProfile;

    let greeting;
    if (isLoggedIn) {
        const name = (profile && profile.full_name)
            ? `, ${profile.full_name.split(' ')[0]}`
            : '';
        const biz = (profile && profile.business_name)
            ? ` for **${profile.business_name}**` : '';

        greeting =
            `Hi${name}! I'm ProfitPilot — your AI business assistant${biz}.\n\n` +
            `I'm connected to your real inventory and sales data. Ask me anything specific to your products, stock, or revenue.\n\n` +
            `Try asking:\n` +
            `  What should I restock?\n` +
            `  What is my best selling product?\n` +
            `  What isn't selling?\n` +
            `  How is my profit this week?\n` +
            `  Any upcoming festival demand?\n` +
            `  Tell me about GST`;
    } else {
        greeting =
            `Hi! I'm ProfitPilot — your AI business assistant.\n\n` +
            `⚠️ You are not signed in. I can only provide general answers right now.\n\n` +
            `**Sign in** to get personalised insights based on your actual inventory, ` +
            `real sales data, and custom business profile.\n\n` +
            `What would you like to know?`;
    }

    appendBotMessage(greeting);

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    });
}

// Wait for Firebase auth to resolve
if (window._authReady) {
    _initChatbot();
} else {
    window.addEventListener('auth-ready', _initChatbot, { once: true });
}

// -- SEND FLOW ----------------------------------------------------------
async function handleSend() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    chatInput.value = '';
    appendUserMessage(msg);

    const typingId = showTyping();

    // Simulate slight thinking delay for premium feel
    await delay(500 + Math.random() * 300);

    try {
        // Use apiCall() so the Authorization header is always included
        // This ensures the backend resolves the real user_id, not 'demo'
        const data = await apiCall('/api/chat', 'POST', { message: msg });
        removeTyping(typingId);
        appendBotMessage(data.response || "I couldn't process that. Please try again.");
    } catch (err) {
        removeTyping(typingId);
        // If auth error, give a meaningful prompt
        if (err.message && err.message.toLowerCase().includes('auth')) {
            appendBotMessage("Please sign in to get personalised business insights based on your inventory.");
        } else {
            appendBotMessage("I'm having trouble connecting to the server. Please try again.");
        }
    }
}

function quickSend(msg) {
    chatInput.value = msg;
    handleSend();
}

// -- MESSAGE RENDERING --------------------------------------------------
function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user-row';

    const initials = window._isLoggedIn && window._userProfile && window._userProfile.full_name
        ? window._userProfile.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
        : 'You';

    row.innerHTML = `
        <div class="msg-avatar user-avatar-sm">${initials}</div>
        <div class="msg-bubble user-bubble">${escHtml(text)}</div>
    `;
    chatWindow.appendChild(row);
    scrollToBottom();
}

function appendBotMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row';
    row.innerHTML = `
        <div class="msg-avatar bot-avatar-sm">AI</div>
        <div class="msg-bubble bot-bubble">${formatBotText(text)}</div>
    `;
    chatWindow.appendChild(row);
    scrollToBottom();
}

// -- TYPING INDICATOR ---------------------------------------------------
function showTyping() {
    const id = 'typing-' + Date.now();
    const row = document.createElement('div');
    row.className = 'msg-row';
    row.id = id;
    row.innerHTML = `
        <div class="msg-avatar bot-avatar-sm">AI</div>
        <div class="msg-bubble bot-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <span style="margin-left:6px; font-size:0.78rem; color:var(--text-muted);">Analyzing your data...</span>
            </div>
        </div>
    `;
    chatWindow.appendChild(row);
    scrollToBottom();
    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// -- HELPERS ------------------------------------------------------------
function scrollToBottom() {
    requestAnimationFrame(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    });
}

// Convert plain text with bullets into readable HTML
function formatBotText(text) {
    let safe = escHtml(text);
    // Bold anything between **
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Lines starting with "  " treated as indented items
    safe = safe.replace(/^  (.+)$/gm, '<span style="display:block; padding: 4px 0 4px 12px; border-left: 2px solid var(--accent-blue); margin: 3px 0;">$1</span>');
    // Newlines to breaks
    safe = safe.replace(/\n/g, '<br>');
    return safe;
}

function escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
