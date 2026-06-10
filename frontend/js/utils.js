// js/utils.js
function showLoading(btn) {
    btn.disabled = true;
    btn.textContent = 'Đang xử lý...';
}
function hideLoading(btn, originalText) {
    btn.disabled = false;
    btn.textContent = originalText;
}
function displayError(element, message) {
    if (element) {
        element.textContent = message;
        element.classList.remove('hidden');
    }
    console.error(message);
}
function clearError(element) {
    if (element) element.classList.add('hidden');
}
function saveUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}
function getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
}
function saveToken(token) {
    localStorage.setItem('access_token', token);
}
function getToken() {
    return localStorage.getItem('access_token');
}
function isAuthenticated() {
    return !!getToken();
}
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'index.html'; // về login
}