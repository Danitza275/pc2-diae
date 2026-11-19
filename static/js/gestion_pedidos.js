/* Gestión de pedidos (Administrador): cambia el estado con PATCH /api/orders/<id>/ */

const tbody = document.querySelector('#tabla-pedidos tbody');
const msg = document.getElementById('pedidos-msg');

const ESTADOS = { pendiente: 'Pendiente', enviado: 'Enviado', entregado: 'Entregado' };

async function cargarPedidos() {
  try {
    const pedidos = await apiFetch('/api/orders/');
    document.getElementById('total-pedidos').textContent = `(${pedidos.length})`;

    if (!pedidos.length) {
      tbody.innerHTML = '<tr><td colspan="6">No hay pedidos.</td></tr>';
      return;
    }

    tbody.innerHTML = pedidos.map(p => {
      const opciones = Object.entries(ESTADOS)
        .map(([valor, texto]) =>
          `<option value="${valor}" ${p.status === valor ? 'selected' : ''}>${texto}</option>`)
        .join('');

      const productos = p.items
        .map(i => `${i.quantity} × ${escapar(i.product_name)}`)
        .join(', ');

      return `
        <tr>
          <td>${p.id}</td>
          <td>${escapar(p.user_name)}</td>
          <td>${formatoFecha(p.created_at)}</td>
          <td class="celda-items">${productos}</td>
          <td>${formatoPrecio(p.total)}</td>
          <td>
            <select class="selector-estado estado-${p.status}" data-id="${p.id}">${opciones}</select>
          </td>
        </tr>`;
    }).join('');
  } catch (error) {
    msg.className = 'mensaje-api error';
    msg.textContent = error.message;
  }
}

tbody.addEventListener('change', async (evento) => {
  const selector = evento.target.closest('select[data-id]');
  if (!selector) return;

  const id = selector.dataset.id;
  const estadoAnterior = selector.classList.contains('estado-pendiente') ? 'pendiente'
    : selector.classList.contains('estado-enviado') ? 'enviado' : 'entregado';
  const nuevoEstado = selector.value;

  try {
    await apiFetch('/api/orders/' + id + '/', {
      metodo: 'PATCH',
      datos: { status: nuevoEstado }
    });
    selector.className = 'selector-estado estado-' + nuevoEstado;
    msg.className = 'mensaje-api ok';
    msg.textContent = `Pedido #${id} → ${ESTADOS[nuevoEstado]}`;
  } catch (error) {
    selector.value = estadoAnterior;   // si falla, devolvemos el valor anterior
    msg.className = 'mensaje-api error';
    msg.textContent = error.message;
  }
});

cargarPedidos();
