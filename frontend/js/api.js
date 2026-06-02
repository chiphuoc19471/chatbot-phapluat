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
        // FIX 1: Token hết hạn → tự động đăng xuất, không để user kẹt
        if (response.status === 401) {
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

// Chat
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