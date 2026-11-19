/* Gestión de productos (Administrador): alta, edición y borrado por fetch */

const tbody = document.querySelector('#tabla-productos tbody');
const form = document.getElementById('form-producto');
const msgForm = document.getElementById('form-msg');
const msgTabla = document.getElementById('tabla-msg');
const titulo = document.getElementById('form-titulo');

const CAMPOS = {
  id: document.getElementById('prod-id'),
  name: document.getElementById('prod-name'),
  description: document.getElementById('prod-description'),
  price: document.getElementById('prod-price'),
  stock: document.getElementById('prod-stock'),
  category: document.getElementById('prod-category'),
  image: document.getElementById('prod-image'),
  model: document.getElementById('prod-model')
};

let editando = false;
let productos = [];

/* ---------- lista ---------- */

async function cargarProductos() {
  try {
    productos = await apiFetch('/api/products/');
    document.getElementById('total-productos').textContent = `(${productos.length})`;

    if (!productos.length) {
      tbody.innerHTML = '<tr><td colspan="7">No hay productos.</td></tr>';
      return;
    }

    tbody.innerHTML = productos.map(p => `
      <tr>
        <td>${p.image
          ? `<img class="miniatura" src="${escapar(p.image)}" alt="">`
          : '<span class="sin-imagen-mini">📷</span>'}</td>
        <td>${escapar(p.name)}</td>
        <td><span class="etiqueta">${escapar(p.category)}</span></td>
        <td>${formatoPrecio(p.price)}</td>
        <td>${p.stock}</td>
        <td>${p.model_3d_url ? 'Sí' : '—'}</td>
        <td class="celda-acciones">
          <button class="btn-mini" data-accion="editar" data-id="${p.id}">Editar</button>
          <button class="btn-mini btn-rojo" data-accion="eliminar" data-id="${p.id}">Eliminar</button>
        </td>
      </tr>`).join('');
  } catch (error) {
    msgTabla.className = 'mensaje-api error';
    msgTabla.textContent = error.message;
  }
}

/* ---------- acciones de la tabla ---------- */

tbody.addEventListener('click', async (evento) => {
  const boton = evento.target.closest('button[data-accion]');
  if (!boton) return;

  const producto = productos.find(p => p.id === Number(boton.dataset.id));
  if (!producto) return;

  if (boton.dataset.accion === 'editar') {
    editando = true;
    titulo.textContent = `Editar producto: ${producto.name}`;
    msgForm.textContent = '';
    CAMPOS.id.value = producto.id;
    CAMPOS.name.value = producto.name;
    CAMPOS.description.value = producto.description || '';
    CAMPOS.price.value = producto.price;
    CAMPOS.stock.value = producto.stock;
    CAMPOS.category.value = producto.category;
    CAMPOS.model.value = producto.model_3d_url || '';
    CAMPOS.image.value = '';
    form.scrollIntoView({ behavior: 'smooth' });
  }

  if (boton.dataset.accion === 'eliminar') {
    if (!confirm(`¿Eliminar el producto "${producto.name}"?`)) return;
    try {
      await apiFetch('/api/products/' + producto.id + '/', { metodo: 'DELETE' });
      await cargarProductos();
    } catch (error) {
      msgTabla.className = 'mensaje-api error';
      msgTabla.textContent = error.message;
    }
  }
});

/* ---------- formulario ---------- */

form.addEventListener('submit', async (evento) => {
  evento.preventDefault();
  msgForm.className = 'mensaje-api';
  msgForm.textContent = '';

  const datos = new FormData();
  datos.append('name', CAMPOS.name.value);
  datos.append('description', CAMPOS.description.value);
  datos.append('price', CAMPOS.price.value);
  datos.append('stock', CAMPOS.stock.value);
  datos.append('category', CAMPOS.category.value);
  datos.append('model_3d_url', CAMPOS.model.value);
  if (CAMPOS.image.files.length) datos.append('image', CAMPOS.image.files[0]);

  try {
    if (editando) {
      await apiFetch('/api/products/' + CAMPOS.id.value + '/', { metodo: 'PATCH', datos, archivo: true });
    } else {
      await apiFetch('/api/products/', { metodo: 'POST', datos, archivo: true });
    }
    limpiarFormulario();
    await cargarProductos();
  } catch (error) {
    msgForm.className = 'mensaje-api error';
    msgForm.textContent = error.message;
  }
});

function limpiarFormulario() {
  form.reset();
  CAMPOS.id.value = '';
  editando = false;
  titulo.textContent = 'Nuevo producto';
}

document.getElementById('btn-cancelar').addEventListener('click', limpiarFormulario);

cargarProductos();
