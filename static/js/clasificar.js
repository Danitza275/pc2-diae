/* Página /clasificar/: sube una imagen y la analiza POST /api/clasificar/ */

const archivo = document.getElementById('archivo');
const textoArchivo = document.getElementById('texto-archivo');
const cajaPrev = document.getElementById('vista-previa');
const imgPrev = document.getElementById('imagen-previa');
const btn = document.getElementById('btn-analizar');
const msg = document.getElementById('clasificar-msg');
const resultado = document.getElementById('resultado');
const barras = document.getElementById('barras');
const relacionados = document.getElementById('relacionados');
const modelo = document.getElementById('modelo');

let imagenSeleccionada = null;
let urlPrevista = null;

/* ---------- selección + vista previa ---------- */

archivo.addEventListener('change', () => {
  const elegido = archivo.files[0];

  if (!elegido) return;

  if (!elegido.type.startsWith('image/')) {
    msg.className = 'mensaje-api error';
    msg.textContent = 'El archivo elegido no es una imagen.';
    archivo.value = '';
    return;
  }

  imagenSeleccionada = elegido;
  if (urlPrevista) URL.revokeObjectURL(urlPrevista);
  urlPrevista = URL.createObjectURL(elegido);
  imgPrev.src = urlPrevista;
  cajaPrev.hidden = false;
  textoArchivo.textContent = elegido.name;
  btn.disabled = false;
  resultado.hidden = true;
  msg.className = 'mensaje-api';
  msg.textContent = '';
});

/* ---------- analizar ---------- */

btn.addEventListener('click', async () => {
  if (!imagenSeleccionada) return;

  btn.disabled = true;
  btn.textContent = 'Analizando…';
  resultado.hidden = true;
  msg.className = 'mensaje-api cargando';
  msg.textContent = 'Analizando la imagen con Hugging Face… puede tardar unos segundos.';

  try {
    const datos = new FormData();
    datos.append('image', imagenSeleccionada);

    const respuesta = await apiFetch('/api/clasificar/', {
      metodo: 'POST', datos, archivo: true
    });

    msg.textContent = '';
    pintarResultados(respuesta);
  } catch (error) {
    msg.className = 'mensaje-api error';
    msg.textContent = 'No se pudo analizar la imagen: ' + error.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analizar';
  }
});

/* ---------- pintado ---------- */

function pintarResultados(respuesta) {
  modelo.textContent = 'Modelo: ' + respuesta.modelo;

  barras.innerHTML = respuesta.etiquetas.map(etiqueta => {
    const porcentaje = (etiqueta.score * 100).toFixed(1);
    return `
      <div class="barra-fila">
        <span class="barra-etiqueta">${escapar(etiqueta.label)}</span>
        <div class="barra">
          <div class="barra-relleno" style="width: ${porcentaje}%"></div>
        </div>
        <span class="barra-valor">${porcentaje}%</span>
      </div>`;
  }).join('');

  const productos = respuesta.productos_relacionados;
  if (!productos.length) {
    relacionados.innerHTML = '<p class="texto-suave">No se encontraron productos relacionados en el catálogo.</p>';
  } else {
    relacionados.innerHTML = productos.map(p => `
      <article class="tarjeta">
        ${p.image
          ? `<img src="${escapar(p.image)}" alt="${escapar(p.name)}">`
          : '<div class="sin-imagen">📷</div>'}
        <div class="tarjeta-cuerpo">
          <span class="etiqueta">${escapar(p.category)}</span>
          <h3>${escapar(p.name)}</h3>
          <p class="descripcion">${escapar(p.description || 'Sin descripción.')}</p>
          <div class="precio">${formatoPrecio(p.price)}</div>
          <div class="detalle">
            ${p.stock > 0 ? `<span class="disponible">Stock: ${p.stock}</span>`
                          : '<span class="agotado">Agotado</span>'}
          </div>
        </div>
      </article>`).join('');
  }

  resultado.hidden = false;
}
