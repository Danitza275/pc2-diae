/* ============================================================
   Helpers compartidos: token CSRF y llamadas a la API
   ============================================================ */

// Lee el token CSRF de la cookie que Django deja en el navegador
function tokenCsrf() {
  const cookies = document.cookie ? document.cookie.split('; ') : [];
  for (const c of cookies) {
    const [clave, valor] = c.split('=');
    if (clave === 'csrftoken') return decodeURIComponent(valor);
  }
  return '';
}

// Convierte la respuesta de error de la API en un mensaje legible
function mensajeError(cuerpo) {
  if (!cuerpo) return 'Error inesperado.';
  if (typeof cuerpo === 'string') return cuerpo;
  if (cuerpo.detail) return cuerpo.detail;
  if (Array.isArray(cuerpo)) return cuerpo.join(' ');
  return Object.entries(cuerpo)
    .map(([campo, valor]) => `${campo}: ${Array.isArray(valor) ? valor.join(' ') : JSON.stringify(valor)}`)
    .join(' | ');
}

// Llamada fetch con sesión y CSRF incluidos
async function apiFetch(ruta, { metodo = 'GET', datos = null, archivo = false } = {}) {
  const opciones = {
    method: metodo,
    credentials: 'same-origin',
    headers: {}
  };

  if (datos !== null) {
    if (archivo) {
      opciones.body = datos;                 // FormData: el navegador pone el Content-Type
    } else {
      opciones.headers['Content-Type'] = 'application/json';
      opciones.body = JSON.stringify(datos);
    }
  }

  if (metodo !== 'GET') {
    opciones.headers['X-CSRFToken'] = tokenCsrf();
  }

  const respuesta = await fetch(ruta, opciones);
  let cuerpo = null;
  try { cuerpo = await respuesta.json(); } catch (e) { cuerpo = null; }

  if (!respuesta.ok) {
    throw new Error(mensajeError(cuerpo) || 'HTTP ' + respuesta.status);
  }
  return cuerpo;
}

function formatoPrecio(valor) {
  return 'S/ ' + Number(valor).toFixed(2);
}

// Evita inyectar HTML en los datos que vienen de la API
function escapar(texto) {
  const div = document.createElement('div');
  div.textContent = texto == null ? '' : String(texto);
  return div.innerHTML;
}

function formatoFecha(iso) {
  return new Date(iso).toLocaleString('es-PE', {
    dateStyle: 'medium', timeStyle: 'short'
  });
}
