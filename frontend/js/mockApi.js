// js/mockApi.js - Mock API
// Chỉ dùng khi CONFIG.USE_MOCK = true
// Các hàm tương tự api.js nhưng dùng dữ liệu giả

let mockConversations = [
    { id: 1, title: 'Thử việc tối đa bao nhiêu ngày?', topic: 'hop-dong', message_count: 2, created_at: '2024-06-15T10:30:00', updated_at: '2024-06-15T10:45:00' },
    { id: 2, title: 'Tính trợ cấp thôi việc thế nào?', topic: 'luong', message_count: 4, created_at: '2024-06-14T09:00:00', updated_at: '2024-06-14T09:20:00' }
];
let mockMessages = {
    1: [
        { id: 1, role: 'user', content: 'Thử việc tối đa bao nhiêu ngày?', sources: null, created_at: '2024-06-15T10:30:00' },
        { id: 2, role: 'assistant', content: 'Theo Điều 25 BLLĐ 2019, thời gian thử việc không quá 180 ngày đối với quản lý...', sources: [{ law: 'BLLĐ 2019', article: 'Điều 25' }], created_at: '2024-06-15T10:30:05' }
    ],
    2: []
};
let nextConvId = 3;
let nextMsgId = 10;

async function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

// Mock login: cho phép bất kỳ email/pass nào cũng thành công (demo)
async function login(email, password) {
    await delay(500);
    if (email === 'demo@example.com' && password === '123') {
        const user = { id: 1, email, name: 'Người dùng demo' };
        saveToken('mock-token');
        saveUser(user);
        return { access_token: 'mock-token', user };
    } else {
        const err = new Error('Sai email hoặc mật khẩu');
        err.status = 401;
        err.data = { detail: 'Sai email hoặc mật khẩu (demo: demo@example.com / 123)' };
        throw err;
    }
}

async function register(email, password, name) {
    await delay(500);
    // giả lập thành công
    return { message: 'Đăng ký thành công', user_id: Math.floor(Math.random() * 1000) };
}

async function sendMessage(question, conversationId = null) {
    await delay(800);
    let conv = mockConversations.find(c => c.id === conversationId);
    if (!conv && conversationId !== null) {
        const err = new Error('Không tìm thấy hội thoại');
        err.status = 404;
        throw err;
    }
    if (!conv) {
        // tạo mới
        conv = {
            id: nextConvId++,
            title: question.length > 50 ? question.slice(0,50)+'...' : question,
            topic: 'khac',
            message_count: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        mockConversations.unshift(conv);
        mockMessages[conv.id] = [];
    }
    // thêm user message
    const userMsg = { id: nextMsgId++, role: 'user', content: question, sources: null, created_at: new Date().toISOString() };
    mockMessages[conv.id].push(userMsg);
    // tạo câu trả lời giả
    const answer = `Trả lời: "${question}". Theo luật lao động, bạn cần tham khảo điều 25.`;
    const assistantMsg = { id: nextMsgId++, role: 'assistant', content: answer, sources: [{ law: 'BLLĐ 2019', article: 'Điều 25' }], created_at: new Date().toISOString() };
    mockMessages[conv.id].push(assistantMsg);
    conv.message_count = mockMessages[conv.id].length;
    conv.updated_at = new Date().toISOString();
    return { answer, sources: assistantMsg.sources, conversation_id: conv.id, message_id: assistantMsg.id };
}

async function getHistoryList() {
    await delay(300);
    return mockConversations.map(c => ({
        id: c.id,
        title: c.title,
        topic: c.topic,
        message_count: c.message_count,
        created_at: c.created_at,
        updated_at: c.updated_at
    }));
}

async function getConversationDetail(convId) {
    await delay(300);
    const conv = mockConversations.find(c => c.id == convId);
    if (!conv) {
        const err = new Error('Không tìm thấy hội thoại');
        err.status = 404;
        throw err;
    }
    return { ...conv, messages: mockMessages[convId] || [] };
}

async function deleteConversation(convId) {
    await delay(300);
    const index = mockConversations.findIndex(c => c.id == convId);
    if (index === -1) {
        const err = new Error('Không tìm thấy');
        err.status = 404;
        throw err;
    }
    mockConversations.splice(index,1);
    delete mockMessages[convId];
    return { message: 'Đã xóa' };
}