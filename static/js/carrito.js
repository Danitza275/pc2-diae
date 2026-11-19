/* ============================================================
   Carrito en localStorage (solo en el navegador, no en la BD)
   ============================================================ */

const CLAVE_CARRITO = 'carrito';

function leerCarrito() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_CARRITO)) || [];
  } catch (e) {
    return [];
  }
}

function guardarCarrito(items) {
  localStorage.setItem(CLAVE_CARRITO, JSON.stringify(items));
  actualizarBadge();
}

function agregarAlCarrito(producto) {
  const carrito = leerCarrito();
  const existente = carrito.find(i => i.id === producto.id);
  if (existente) {
    existente.cantidad += 1;
  } else {
    carrito.push({
      id: producto.id,
      nombre: producto.name,
      precio: Number(producto.price),
      imagen: producto.image || '',
      categoria: producto.category,
      cantidad: 1
    });
  }
  guardarCarrito(carrito);
}

function cambiarCantidad(id, delta) {
  const carrito = leerCarrito();
  const item = carrito.find(i => i.id === id);
  if (!item) return;
  item.cantidad += delta;
  const nuevos = carrito.filter(i => i.cantidad > 0);
  guardarCarrito(nuevos);
}

function quitarDelCarrito(id) {
  guardarCarrito(leerCarrito().filter(i => i.id !== id));
}

function vaciarCarrito() {
  guardarCarrito([]);
}

function totalCarrito() {
  return leerCarrito().reduce((suma, i) => suma + i.precio * i.cantidad, 0);
}

// Número que se muestra en la barra de navegación
function actualizarBadge() {
  const badge = document.getElementById('carrito-num');
  if (!badge) return;
  const total = leerCarrito().reduce((suma, i) => suma + i.cantidad, 0);
  badge.textContent = total;
  badge.style.display = total > 0 ? 'inline-block' : 'none';
}

actualizarBadge();
