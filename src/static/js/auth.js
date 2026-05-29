// Obtiene el token JWT almacenado en el navegador
function getToken() {
    return localStorage.getItem('access_token');
}

// Fetch wrapper que incluye el token JWT en cada peticion
async function apiFetch(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`,
        ...options.headers,
    };
    const response = await fetch(url, { ...options, headers });
    // Si el token expiro, redirige al login
    if (response.status === 401) {
        window.location.href = '/login/';
        return;
    }
    return response;
}
