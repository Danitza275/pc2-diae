/* Mis pedidos: GET /api/orders/ (la API devuelve solo los del usuario) */

const lista = document.getElementById('pedidos-lista');
const msg = document.getElementById('pedidos-msg');

const ESTADOS = { pendiente: 'Pendiente', enviado: 'Enviado', entregado: 'Entregado' };

async function cargarPedidos() {
  try {
    const pedidos = await apiFetch('/api/orders/');

    if (!pedidos.length) {
      msg.textContent = 'Todavía no has hecho pedidos.';
      return;
    }
    msg.textContent = `${pedidos.length} pedido(s)`;

    lista.innerHTML = pedidos.map(pedido => {
      const productos = pedido.items.map(item =>
        `<li>${item.quantity} × ${escapar(item.product_name)} — ${formatoPrecio(item.unit_price)}</li>`
      ).join('');

      return `
        <article class="pedido">
          <header class="pedido-cabecera">
            <strong>Pedido #${pedido.id}</strong>
            <span class="estado estado-${pedido.status}">${ESTADOS[pedido.status] || pedido.status}</span>
            <span class="texto-suave">${formatoFecha(pedido.created_at)}</span>
            <strong class="precio">${formatoPrecio(pedido.total)}</strong>
          </header>
          <ul class="pedido-items">${productos}</ul>
        </article>`;
    }).join('');
  } catch (error) {
    msg.className = 'mensaje-api error';
    msg.textContent = 'No se pudieron cargar tus pedidos: ' + error.message;
  }
}

cargarPedidos();
