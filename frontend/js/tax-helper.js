/**
 * tax-helper.js — Floating "Ask AI" helper panel for the Tax page.
 * Sends questions to /api/chat and renders plain-language responses.
 */
(function() {
  // Inject floating button + panel
  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <button id="tax-helper-btn" style="
      position:fixed; bottom:24px; right:24px; z-index:1000;
      background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff;
      border:none; border-radius:28px; padding:12px 20px;
      font-size:0.88rem; font-weight:600; cursor:pointer;
      box-shadow:0 6px 24px rgba(37,99,235,0.35);
      display:flex; align-items:center; gap:8px;
      transition:all 0.3s; font-family:var(--font-body,'DM Sans',sans-serif);
    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Need help understanding?
    </button>

    <div id="tax-helper-panel" style="
      display:none; position:fixed; bottom:80px; right:24px; z-index:1001;
      width:360px; max-height:480px; background:#fff;
      border:1px solid rgba(37,99,235,0.15); border-radius:16px;
      box-shadow:0 16px 48px rgba(0,0,0,0.14);
      font-family:var(--font-body,'DM Sans',sans-serif);
      overflow:hidden; animation:taxHelperSlideIn 0.3s ease;
    ">
      <div style="padding:14px 18px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:#fff; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div style="font-weight:700; font-size:0.95rem;">Tax & Finance Helper</div>
          <div style="font-size:0.75rem; opacity:0.8;">Ask anything in simple language</div>
        </div>
        <button id="tax-helper-close" style="background:none;border:none;color:#fff;cursor:pointer;font-size:1.2rem;padding:4px;">✕</button>
      </div>
      <div id="tax-helper-messages" style="padding:14px; max-height:320px; overflow-y:auto; display:flex; flex-direction:column; gap:10px;">
        <div style="background:rgba(37,99,235,0.06); padding:10px 14px; border-radius:12px; font-size:0.85rem; line-height:1.5; color:#334155;">
          Hi! Ask me anything about your taxes. Try:<br>
          <span style="color:#2563eb; cursor:pointer;" class="tax-quick-q">"What is Section 44AD?"</span><br>
          <span style="color:#2563eb; cursor:pointer;" class="tax-quick-q">"Explain GST Composition Scheme"</span><br>
          <span style="color:#2563eb; cursor:pointer;" class="tax-quick-q">"What is Input Tax Credit?"</span><br>
          <span style="color:#2563eb; cursor:pointer;" class="tax-quick-q">"Tell me about Section 87A rebate"</span>
        </div>
      </div>
      <div style="padding:10px 14px; border-top:1px solid rgba(0,0,0,0.06); display:flex; gap:8px;">
        <input type="text" id="tax-helper-input" placeholder="Ask about GST, income tax, 44AD..." style="
          flex:1; padding:10px 14px; border:1px solid rgba(0,0,0,0.1); border-radius:10px;
          font-size:0.88rem; outline:none; font-family:inherit;
        ">
        <button id="tax-helper-send" style="
          background:#2563eb; color:#fff; border:none; border-radius:10px;
          padding:10px 14px; cursor:pointer; font-weight:600; font-size:0.85rem;
        ">Send</button>
      </div>
    </div>
  `;
  document.body.appendChild(wrapper);

  // Add animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes taxHelperSlideIn { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
    @media (max-width: 480px) {
      #tax-helper-panel { width:calc(100vw - 32px) !important; right:16px !important; bottom:70px !important; }
      #tax-helper-btn { right:16px !important; bottom:16px !important; padding:10px 16px !important; font-size:0.82rem !important; }
    }
  `;
  document.head.appendChild(style);

  // Toggle panel
  document.getElementById('tax-helper-btn').onclick = () => {
    const panel = document.getElementById('tax-helper-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  };
  document.getElementById('tax-helper-close').onclick = () => {
    document.getElementById('tax-helper-panel').style.display = 'none';
  };

  // Quick question clicks
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('tax-quick-q')) {
      const q = e.target.textContent.replace(/^"|"$/g, '');
      document.getElementById('tax-helper-input').value = q;
      sendTaxQuestion();
    }
  });

  // Send
  document.getElementById('tax-helper-send').onclick = sendTaxQuestion;
  document.getElementById('tax-helper-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendTaxQuestion();
  });

  async function sendTaxQuestion() {
    const input = document.getElementById('tax-helper-input');
    const q = input.value.trim();
    if (!q) return;
    input.value = '';

    const msgArea = document.getElementById('tax-helper-messages');

    // User message
    msgArea.innerHTML += `
      <div style="align-self:flex-end; background:var(--accent-blue,#2563eb); color:#fff; padding:8px 14px; border-radius:12px 12px 2px 12px; font-size:0.85rem; max-width:85%;">
        ${q}
      </div>
    `;
    msgArea.scrollTop = msgArea.scrollHeight;

    // Loading
    const loadId = 'load-' + Date.now();
    msgArea.innerHTML += `<div id="${loadId}" style="align-self:flex-start; color:var(--text-muted); font-size:0.82rem; padding:6px 12px;">Thinking...</div>`;
    msgArea.scrollTop = msgArea.scrollHeight;

    try {
      const res = await (window.apiCall ? apiCall('/api/chat', 'POST', { message: q }) : fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: q }) }).then(r => r.json()));

      const loadEl = document.getElementById(loadId);
      if (loadEl) loadEl.remove();

      const reply = res.response || res.error || 'Sorry, I could not get an answer.';
      const formatted = reply.replace(/\\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

      msgArea.innerHTML += `
        <div style="align-self:flex-start; background:rgba(37,99,235,0.06); padding:10px 14px; border-radius:12px 12px 12px 2px; font-size:0.85rem; line-height:1.55; max-width:92%; color:#334155;">
          ${formatted}
        </div>
      `;
    } catch (err) {
      const loadEl = document.getElementById(loadId);
      if (loadEl) loadEl.remove();
      msgArea.innerHTML += `<div style="color:var(--accent-red); font-size:0.82rem; padding:6px 12px;">Failed to get response. Please try again.</div>`;
    }
    msgArea.scrollTop = msgArea.scrollHeight;
  }
})();
