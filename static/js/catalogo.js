/* Catálogo de productos: consume la API con fetch() */

const contenedor = document.getElementById('productos');
const mensaje = document.getElementById('mensaje');

const ETIQUETAS = {
  celulares: 'Celulares',
  laptops: 'Laptops',
  audifonos: 'Audífonos',
  accesorios: 'Accesorios',
  otros: 'Otros'
};

function tarjeta(producto) {
  const imagen = producto.image
    ? `<img src="${escapar(producto.image)}" alt="${escapar(producto.name)}">`
    : `<div class="sin-imagen">📷</div>`;

  const stock = producto.stock > 0
    ? `<span class="disponible">Stock: ${producto.stock}</span>`
    : `<span class="agotado">Agotado</span>`;

  // El botón solo aparece para clientes (data-comprar="1")
  const puedeComprar = contenedor.dataset.comprar === '1' && producto.stock > 0;
  const boton = puedeComprar
    ? `<button class="btn btn-agregar" data-id="${producto.id}">Agregar al carrito</button>`
    : '';

  return `
    <article class="tarjeta">
      ${imagen}
      <div class="tarjeta-cuerpo">
        <span class="etiqueta">${ETIQUETAS[producto.category] || escapar(producto.category)}</span>
        <h3>${escapar(producto.name)}</h3>
        <p class="descripcion">${escapar(producto.description || 'Sin descripción.')}</p>
        <div class="precio">S/ ${Number(producto.price).toFixed(2)}</div>
        <div class="detalle">${stock}</div>
        ${boton}
      </div>
    </article>`;
}

// Delegación de eventos: el botón está dentro de la tarjeta
contenedor.addEventListener('click', (evento) => {
  const boton = evento.target.closest('.btn-agregar');
  if (!boton) return;
  const producto = productosCargados.find(p => p.id === Number(boton.dataset.id));
  if (!producto) return;
  agregarAlCarrito(producto);
  boton.textContent = '✓ Agregado';
  setTimeout(() => { boton.textContent = 'Agregar al carrito'; }, 900);
});

let productosCargados = [];

async function cargarProductos() {
  try {
    const respuesta = await fetch('/api/products/');

    if (respuesta.status === 403) {
      mensaje.innerHTML = 'Para ver el catálogo debes <a href="/accounts/login/">iniciar sesión</a>.';
      return;
    }
    if (!respuesta.ok) {
      throw new Error('HTTP ' + respuesta.status);
    }

    const productos = await respuesta.json();
    if (!productos.length) {
      mensaje.textContent = 'No hay productos disponibles.';
      return;
    }

    productosCargados = productos;
    mensaje.remove();
    contenedor.innerHTML = productos.map(tarjeta).join('');
  } catch (error) {
    mensaje.textContent = 'No se pudo cargar el catálogo: ' + error.message;
  }
}

cargarProductos();
