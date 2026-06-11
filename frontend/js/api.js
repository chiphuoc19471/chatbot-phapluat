// js/api.js
async function request(endpoint, method = 'GET', body = null, needAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (needAuth) {
        const token = getToken();
        if (!token) throw new Error('Chưa đăng nhập');
        headers['Authorization'] = `Bearer ${token}`;
    }
    const options = {
        method,
        headers,
    };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${CONFIG.BASE_URL}${endpoint}`, options);
    const data = await response.json();
    if (!response.ok) {
        // FIX 1: Token hết hạn → tự động đăng xuất, không để user kẹt (trừ khi ở endpoint đăng nhập)
        if (response.status === 401 && endpoint !== '/auth/login') {
            logout();
            return;
        }
        const err = new Error(data.detail || 'Lỗi kết nối');
        err.status = response.status;
        err.data = data;
        throw err;
    }
    return data;
}

// Auth
async function register(email, password, name) {
    return request('/auth/register', 'POST', { email, password, name }, false);
}
async function login(email, password) {
    const data = await request('/auth/login', 'POST', { email, password }, false);
    saveToken(data.access_token);
    saveUser(data.user);
    return data;
}

// Chat - streaming version
async function* sendMessageStream(question, conversationId = null) {
    const token = getToken();
    if (!token) throw new Error('Chưa đăng nhập');
    const body = { question };
    if (conversationId) body.conversation_id = conversationId;

    const response = await fetch(`${CONFIG.BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        if (response.status === 401) { logout(); return; }
        throw new Error('Lỗi kết nối');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try { yield JSON.parse(line.slice(6)); } catch (_) {}
            }
        }
    }
}

// Chat - non-streaming (fallback)
async function sendMessage(question, conversationId = null) {
    // FIX 2: Không gửi conversation_id: null lên backend
    // FastAPI/Pydantic có thể báo lỗi validation nếu nhận null thay vì bỏ trống field
    const body = { question };
    if (conversationId) body.conversation_id = conversationId;
    return request('/chat', 'POST', body, true);
}

// History
async function getHistoryList() {
    return request('/history', 'GET', null, true);
}
async function getConversationDetail(convId) {
    return request(`/history/${convId}`, 'GET', null, true);
}
async function deleteConversation(convId) {
    return request(`/history/${convId}`, 'DELETE', null, true);
}