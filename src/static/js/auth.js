// Obtiene el token JWT almacenado en el navegador
function getToken() {
    return localStorage.getItem('access_token');
}

// Obtiene el valor de una cookie por su nombre
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Fetch wrapper que incluye el token JWT o el CSRF token
async function apiFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    
    const token = getToken();
    if (token && token !== 'null') {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        headers['X-CSRFToken'] = csrftoken;
    }

    const response = await fetch(url, { ...options, headers });
    // Si el token expiro y era 401, redirige al login
    if (response.status === 401) {
        window.location.href = '/login/';
        return;
    }
    return response;
}
