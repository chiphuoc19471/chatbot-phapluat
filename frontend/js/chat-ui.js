// js/chat-ui.js
let currentConversationId = null;
let currentMessages = [];

window.addEventListener('api-ready', async () => {
    // Kiểm tra đăng nhập
    if (!isAuthenticated()) {
        window.location.href = '/';
        return;
    }

    // Load danh sách hội thoại
    await loadHistory();
    setupEventListeners();

    // Nếu không có hội thoại nào, tạo mới (chờ người dùng nhập)
});

async function loadHistory() {
    try {
        const history = await window.getHistoryList();
        renderHistory(history);
        if (history.length > 0) {
            // Tự động chọn hội thoại đầu tiên
            await loadConversation(history[0].id);
        } else {
            // Không có, hiển thị trống
            currentConversationId = null;
            currentMessages = [];
            renderMessages();
        }
    } catch (err) {
        console.error(err);
    }
}

function renderHistory(history) {
    const container = document.getElementById('historyList');
    if (!container) return;
    container.innerHTML = '';
    history.forEach(conv => {
        const div = document.createElement('div');
        div.className = 'history-item';
        if (currentConversationId === conv.id) div.classList.add('active');
        div.innerHTML = `
            <div class="history-item-title">${escapeHtml(conv.title)}</div>
            <div class="history-item-meta">${new Date(conv.created_at).toLocaleString()} - ${conv.message_count} tin nhắn</div>
            <button class="delete-history" data-id="${conv.id}">🗑️</button>
        `;
        div.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-history')) return;
            loadConversation(conv.id);
        });
        const delBtn = div.querySelector('.delete-history');
        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('Xóa hội thoại này?')) {
                await window.deleteConversation(conv.id);
                await loadHistory();
                if (currentConversationId === conv.id) {
                    currentConversationId = null;
                    currentMessages = [];
                    renderMessages();
                }
            }
        });
        container.appendChild(div);
    });
}

async function loadConversation(convId) {
    try {
        const detail = await window.getConversationDetail(convId);
        currentConversationId = detail.id;
        currentMessages = detail.messages || [];
        renderMessages();
        // Cập nhật active trong sidebar
        document.querySelectorAll('.history-item').forEach(el => {
            const btn = el.querySelector('.delete-history');
            const id = btn ? btn.getAttribute('data-id') : null;
            if (id == convId) el.classList.add('active');
            else el.classList.remove('active');
        });
    } catch (err) {
        console.error(err);
    }
}

function renderMessages() {
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    if (currentMessages.length === 0) {
        container.innerHTML = '<div class="empty-chat">Hãy gửi câu hỏi để bắt đầu</div>';
        return;
    }
    container.innerHTML = '';
    currentMessages.forEach(msg => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${msg.role}`;
        let sourcesHtml = '';
        if (msg.sources && msg.sources.length > 0) {
            sourcesHtml = `<div class="message-sources">📚 Nguồn: ${msg.sources.map(s => `${s.law} ${s.article}`).join(', ')}</div>`;
        }
        // FIX 3: escapeHtml trước rồi mới convert \n → <br>
        // Thứ tự quan trọng: escape trước để tránh XSS, sau đó mới format
        const safeContent = escapeHtml(msg.content).replace(/\n/g, '<br>');
        msgDiv.innerHTML = `<div class="message-content">${safeContent}${sourcesHtml}</div>`;
        container.appendChild(msgDiv);
    });
    container.scrollTop = container.scrollHeight;
}

function setupEventListeners() {
    const sendBtn = document.getElementById('sendBtn');
    const input = document.getElementById('messageInput');
    const newChatBtn = document.getElementById('newChatBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    sendBtn.addEventListener('click', sendMessageHandler);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessageHandler();
        }
    });
    newChatBtn.addEventListener('click', () => {
        currentConversationId = null;
        currentMessages = [];
        renderMessages();
        // reload history để thấy cập nhật sau khi gửi tin nhắn đầu
    });
    logoutBtn.addEventListener('click', () => {
        logout();
    });
}

async function sendMessageHandler() {
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    const question = input.value.trim();
    if (!question) return;

    // FIX 4: Disable input + nút trong lúc chờ response, tránh gửi trùng
    input.disabled = true;
    sendBtn.disabled = true;

    input.value = '';
    // Thêm tin nhắn user tạm thời
    const tempUserMsg = { id: Date.now(), role: 'user', content: question, sources: null, created_at: new Date().toISOString() };
    currentMessages.push(tempUserMsg);
    renderMessages();
    // Hiển thị loading
    const loadingMsg = { id: Date.now()+1, role: 'assistant', content: 'Đang suy nghĩ...', sources: null };
    currentMessages.push(loadingMsg);
    renderMessages();
    try {
        const response = await window.sendMessage(question, currentConversationId);
        // Xóa tin nhắn loading
        currentMessages.pop();

        const assistantMsg = {
            id: response.message_id,
            role: 'assistant',
            content: response.answer,
            sources: response.sources,
            created_at: new Date().toISOString()
        };
        currentMessages.push(assistantMsg);

        // Cập nhật conversation_id nếu là hội thoại mới
        if (!currentConversationId) {
            currentConversationId = response.conversation_id;
        }

        renderMessages();

        // FIX 5: Luôn reload sidebar để message_count luôn đúng
        // (cả hội thoại mới lẫn hội thoại cũ đều cần cập nhật)
        await loadHistory();

    } catch (err) {
        currentMessages.pop(); // bỏ loading
        const errorMsg = { id: Date.now(), role: 'assistant', content: `Lỗi: ${err.message || 'Không thể gửi câu hỏi'}`, sources: null };
        currentMessages.push(errorMsg);
        renderMessages();
    } finally {
        // FIX 4: Luôn bật lại input dù thành công hay lỗi
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}