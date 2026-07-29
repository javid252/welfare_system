/**
 * Shared axios instance for all Vue components.
 * Reads the Django CSRF token from the cookie set by {% csrf_token %} /
 * CsrfViewMiddleware and attaches it as X-CSRFToken on every unsafe request,
 * matching CSRF_HEADER_NAME in settings.py.
 */
function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
}

const api = axios.create({
    baseURL: "/api/",
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFToken",
});

api.interceptors.request.use((config) => {
    const token = getCookie("csrftoken");
    if (token) {
        config.headers["X-CSRFToken"] = token;
    }
    return config;
});

window.api = api;
