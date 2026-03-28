const chatWindow = document.getElementById('chat-window');
const chatInput  = document.getElementById('chat-input');

// ─── BOOT ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    appendBotMessage(
        "Hi! I'm ProfitPilot — your business decision assistant.\n\n" +
        "I can tell you what to restock, what's selling, what festivals are coming, " +
        "and guide every business decision — based on your real data.\n\n" +
        "What do you want to know?"
    );

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    });
});

// ─── SEND FLOW ────────────────────────────────────────────────────────
async function handleSend() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    chatInput.value = '';
    appendUserMessage(msg);

    const typingId = showTyping();

    // Simulate slight thinking delay for premium feel
    await delay(600 + Math.random() * 400);

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        removeTyping(typingId);
        appendBotMessage(data.response || "I couldn't process that. Please try again.");
    } catch (err) {
        removeTyping(typingId);
        appendBotMessage("I'm having trouble connecting to the server. Please try again.");
    }
}

function quickSend(msg) {
    chatInput.value = msg;
    handleSend();
}

// ─── MESSAGE RENDERING ────────────────────────────────────────────────
function appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'msg-row user-row';
    row.innerHTML = `
        <div class="msg-avatar user-avatar-sm">You</div>
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

// ─── TYPING INDICATOR ─────────────────────────────────────────────────
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
                <span style="margin-left:6px; font-size:0.8rem; color:var(--text-muted);">Analyzing your business data…</span>
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

// ─── HELPERS ──────────────────────────────────────────────────────────
function scrollToBottom() {
    ChatWindow_requestAnimationFrame(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    });
}

// Polyfill wrapper
function ChatWindow_requestAnimationFrame(cb) {
    if (window.requestAnimationFrame) requestAnimationFrame(cb);
    else setTimeout(cb, 16);
}

// Convert plain text with bullets into readable HTML
function formatBotText(text) {
    // Escape HTML first
    let safe = escHtml(text);
    // Bold anything between **
    safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Bullet points • → visible list items
    safe = safe.replace(/^• (.+)$/gm, '<span style="display:block; padding: 3px 0 3px 4px; border-left: 2px solid var(--accent-orange); margin: 4px 0; padding-left:10px;">$1</span>');
    // Newlines → breaks
    safe = safe.replace(/\n/g, '<br>');
    return safe;
}

function escHtml(str) {
    return String(str)
        .replace(/&/g,'&amp;')
        .replace(/</g,'&lt;')
        .replace(/>/g,'&gt;')
        .replace(/"/g,'&quot;');
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
