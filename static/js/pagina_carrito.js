/* Página del carrito: pide confirmar y crea el pedido con POST /api/orders/ */

const lista = document.getElementById('carrito-lista');
const msg = document.getElementById('carrito-msg');

function pintar() {
  const carrito = leerCarrito();

  if (!carrito.length) {
    lista.innerHTML = `
      <p class="texto-suave">Tu carrito está vacío.</p>
      <a class="btn" href="/">Volver al catálogo</a>`;
    return;
  }

  const filas = carrito.map(item => `
    <div class="carrito-item">
      ${item.imagen
        ? `<img src="${escapar(item.imagen)}" alt="${escapar(item.nombre)}">`
        : `<div class="sin-imagen-mini">📷</div>`}
      <div class="carrito-info">
        <strong>${escapar(item.nombre)}</strong>
        <span class="texto-suave">${formatoPrecio(item.precio)} c/u</span>
      </div>
      <div class="cantidad">
        <button class="btn-mini" data-accion="menos" data-id="${item.id}">−</button>
        <span>${item.cantidad}</span>
        <button class="btn-mini" data-accion="mas" data-id="${item.id}">+</button>
      </div>
      <div class="carrito-subtotal">${formatoPrecio(item.precio * item.cantidad)}</div>
      <button class="btn-mini btn-rojo" data-accion="quitar" data-id="${item.id}">✕</button>
    </div>`).join('');

  lista.innerHTML = `
    ${filas}
    <div class="carrito-total">
      <span>Total</span>
      <strong>${formatoPrecio(totalCarrito())}</strong>
    </div>
    <div class="fila-botones">
      <button id="btn-confirmar" class="btn">Confirmar pedido</button>
      <button id="btn-vaciar" class="btn btn-suave">Vaciar carrito</button>
      <a class="btn btn-suave" href="/">Seguir comprando</a>
    </div>`;
}

lista.addEventListener('click', async (evento) => {
  const boton = evento.target.closest('button[data-accion]');
  if (boton) {
    const id = Number(boton.dataset.id);
    if (boton.dataset.accion === 'mas') cambiarCantidad(id, 1);
    if (boton.dataset.accion === 'menos') cambiarCantidad(id, -1);
    if (boton.dataset.accion === 'quitar') quitarDelCarrito(id);
    msg.textContent = '';
    pintar();
    return;
  }

  if (evento.target.id === 'btn-vaciar') {
    vaciarCarrito();
    msg.textContent = '';
    pintar();
    return;
  }

  if (evento.target.id === 'btn-confirmar') {
    const carrito = leerCarrito();
    if (!carrito.length) return;

    const btn = evento.target;
    btn.disabled = true;
    btn.textContent = 'Enviando…';
    msg.textContent = '';
    msg.className = 'mensaje-api';

    try {
      const items = carrito.map(i => ({ product: i.id, quantity: i.cantidad }));
      const pedido = await apiFetch('/api/orders/', { metodo: 'POST', datos: { items } });
      vaciarCarrito();
      msg.className = 'mensaje-api ok';
      msg.innerHTML = `✓ Pedido #${pedido.id} creado: <strong>${formatoPrecio(pedido.total)}</strong>. ` +
                      `<a href="/mis-pedidos/">Ver mis pedidos</a>`;
      pintar();
    } catch (error) {
      msg.className = 'mensaje-api error';
      msg.textContent = 'No se pudo crear el pedido: ' + error.message;
      btn.disabled = false;
      btn.textContent = 'Confirmar pedido';
    }
  }
});

pintar();
