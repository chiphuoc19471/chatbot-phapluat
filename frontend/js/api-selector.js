// js/api-selector.js
(async function() {
    if (CONFIG.USE_MOCK) {
        await loadScript('js/mockApi.js?v=3');
    } else {
        await loadScript('js/api.js?v=3');
    }
    // Sau khi load xong, các hàm (login, sendMessage, ...) đã có trên window
    window.apiReady = true;
    // dispatch event
    window.dispatchEvent(new Event('api-ready'));
})();

function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}