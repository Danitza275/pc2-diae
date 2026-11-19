# SmartTech Store

Tienda de tecnología hecha con **Django + Django REST Framework + SQLite**, frontend en
templates de Django con HTML/CSS/JavaScript puro (`fetch` a la API), clasificación de
imágenes con el modelo **ViT de Hugging Face** y carrito/pedidos en el navegador.
Todo corre en local: sin GPU, sin Docker y sin servicios en la nube.

---

## 1. Instalación (Fedora)

```bash
sudo dnf install python3 python3-pip git     # si aún no los tienes
git clone <url-del-repositorio> practica2
cd practica2

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env y pon tu propia SECRET_KEY (y HF_TOKEN si usas la API de Hugging Face)
```

## 2. Cómo correr

```bash
source venv/bin/activate

python manage.py migrate        # crea las tablas en db.sqlite3
python manage.py setup_roles    # crea los grupos Administrador y Cliente
python manage.py seed_data      # carga datos de prueba (30 productos, 40 pedidos)
python manage.py runserver      # abre http://127.0.0.1:8000
```

Para recargar los datos desde cero: `python manage.py seed_data --reset`
El modelo de clasificación (330 MB) se descarga solo la primera vez que lo usas.

Opcional: `python manage.py descargar_fotos` reemplaza las imágenes generadas por
fotos reales descargadas de Wikimedia Commons (licencias libres).

## 3. Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `cliente1` … `cliente10` | `cliente123` | Cliente |

## 4. Diagrama del flujo

```
        NAVEGADOR  (templates + static/js con fetch)
        ─────────────────────────────────────────────
        home.html        carrito.html      gestión de productos/pedidos
             │                │                     │
             │ GET            │ POST                │ POST/PATCH/DELETE
             ▼                ▼                     ▼
        ─────────────────────────────────────────────
                  API REST  (/api/…)   DRF + SessionAuthentication
        ─────────────────────────────────────────────
             │                     │
             ▼                     ▼
      ProductViewSet          OrderViewSet ──── valida items
             │                       ├─ calcula total y unit_price (servidor)
             ▼                       └─ descuenta stock (atomic + select_for_update)
      serializers.py  ◄────────────────┘
             │
             ▼
        Modelos (store/models.py)  ──►  SQLite (db.sqlite3)  ──►  media/ (imágenes)

        POST /api/clasificar/  ──►  ViT (ONNX en local, gratis)  ──►  top 5 etiquetas
                                        └─ cruce con name/category  ──►  productos relacionados
```

## 5. Endpoints principales

| Método | Ruta | Quién puede |
|---|---|---|
| GET/POST | `/api/products/` | leer: autenticados · crear: Administrador |
| GET/PATCH/DELETE | `/api/products/<id>/` | Administrador |
| GET | `/api/orders/` | Cliente: solo los suyos · Admin: todos |
| POST | `/api/orders/` | cualquier autenticado (el servidor calcula total y stock) |
| PATCH/DELETE | `/api/orders/<id>/` | Administrador (cambia estado) |
| POST | `/api/clasificar/` | autenticados (multipart con campo `image`) |

## 6. Páginas

`/` catálogo · `/register/` y `/accounts/login/` sesión · `/carrito/` · `/mis-pedidos/` ·
`/clasificar/` análisis de imágenes · `/productos/` y `/pedidos/` (solo Administrador) ·
`/admin/` django admin.
