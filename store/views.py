import io
import os
import re

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import redirect, render
from PIL import Image as PILImage
from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .clasificacion import clasificar_imagen
from .models import Order, Product
from .permissions import EsAdministradorOrReadOnly
from .serializers import (OrderCreateSerializer, OrderSerializer,
                          ProductSerializer)


def home(request):
    """Página de inicio: lista los productos con JavaScript (fetch a /api/products/)."""
    return render(request, 'store/home.html')


def register(request):
    """Registro de nuevos clientes."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)          # queda logueado al registrarse
            return redirect('store:home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def solo_admin(vista):
    """Decorador: solo Administrador, los demás vuelven al inicio."""
    def envuelta(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('store:home')
        return vista(request, *args, **kwargs)
    return envuelta


@login_required
def carrito(request):
    """Página del carrito (los datos viven en localStorage)."""
    return render(request, 'store/carrito.html')


@login_required
def mis_pedidos(request):
    """Pedidos del cliente (los pinta JavaScript con /api/orders/)."""
    return render(request, 'store/mis_pedidos.html')


@solo_admin
def gestion_productos(request):
    """Alta, edición y borrado de productos vía API."""
    return render(request, 'store/gestion_productos.html')


@solo_admin
def gestion_pedidos(request):
    """Todos los pedidos con selector de estado vía API."""
    return render(request, 'store/gestion_pedidos.html')


@login_required
def pagina_clasificar(request):
    """Página para subir una imagen y analizarla con Hugging Face."""
    return render(request, 'store/clasificar.html')


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD de productos: leen los autenticados, escriben los Administradores."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, EsAdministradorOrReadOnly]


class OrderViewSet(viewsets.ModelViewSet):
    """Pedidos: el Cliente solo ve y crea los suyos; el Administrador ve todos
    y puede cambiar el estado (PATCH) o borrar."""

    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def get_permissions(self):
        # Solo el Administrador puede editar o borrar pedidos
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), EsAdministradorOrReadOnly()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Crea el pedido y devuelve el pedido completo (id, total, items)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        data = OrderSerializer(order, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


def explicar_error_hf(error):
    """Convierte una excepción de Hugging Face en un mensaje claro."""
    texto = str(error)
    coincide = re.search(r"'(\d{3}) ([^']+)'", texto)
    if coincide:
        codigo, motivo = coincide.group(1), coincide.group(2)
        if codigo == '401':
            return 'HF_TOKEN inválido o expirado. Revisa el token en el archivo .env.'
        if codigo == '402':
            return ('La cuenta de Hugging Face no tiene créditos de inferencia (402). '
                    'Se necesita una suscripción PRO o créditos para usar la Inference API.')
        if codigo == '429':
            return 'Demasiadas peticiones a Hugging Face (429). Espera un momento e inténtalo de nuevo.'
        if codigo == '404':
            return 'El modelo google/vit-base-patch16-224 no está disponible en este momento (404).'
        return f'Hugging Face respondió {codigo} {motivo}.'
    if 'timed out' in texto.lower() or 'timeout' in texto.lower():
        return 'Hugging Face tardó demasiado en responder. Revisa tu conexión a internet.'
    return 'No se pudo clasificar la imagen: ' + texto.splitlines()[0]


# Palabras en inglés de las etiquetas ImageNet -> palabras de nuestros productos
SINONIMOS = {
    'keyboard': 'teclado', 'keypad': 'teclado', 'typewriter': 'teclado',
    'printer': 'impresora', 'photocopier': 'impresora',
    'phone': 'celular', 'telephone': 'celular', 'cellular': 'celular', 'ipod': 'celular',
    'headphone': 'audifono', 'headphones': 'audifono',
    'earphone': 'audifono', 'earbuds': 'audifono',
    'notebook': 'laptop', 'chromebook': 'laptop', 'macbook': 'laptop',
    'ultrabook': 'laptop', 'computer': 'computadora', 'desktop': 'computadora',
    'loudspeaker': 'parlante', 'speaker': 'parlante',
    'watch': 'reloj', 'clock': 'reloj',
    'joystick': 'consola', 'gamepad': 'consola',
    'memory': 'memoria', 'disk': 'disco', 'drive': 'disco',
    'charger': 'cargador', 'webcam': 'webcam', 'tablet': 'tablet',
    'microphone': 'microfono', 'earphone': 'audifono',
}


def productos_relacionados(etiqueta):
    """Cruza la etiqueta principal con los productos: por cada palabra de la
    etiqueta (y sus sinónimos en español) busca en name o category con icontains."""
    palabras = {p for p in re.split(r'[^a-z0-9]+', etiqueta.lower()) if len(p) >= 3}
    palabras |= {SINONIMOS[p] for p in palabras if p in SINONIMOS}

    ids = set()
    for palabra in palabras:
        ids.update(Product.objects.filter(
            Q(name__icontains=palabra) | Q(category__icontains=palabra)
        ).values_list('id', flat=True))
    return Product.objects.filter(id__in=ids)[:8]


class ClasificarImagen(APIView):
    """POST /api/clasificar/ -> clasifica una imagen con el modelo ViT
    google/vit-base-patch16-224 (in local con ONNX Runtime; si falla, usa la
    Inference API de Hugging Face con HF_TOKEN)."""

    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1) Imagen adjunta
        archivo = request.FILES.get('image')
        if archivo is None:
            return Response(
                {'detail': "Falta la imagen: envía un archivo multipart con el campo 'image'."},
                status=status.HTTP_400_BAD_REQUEST)

        try:
            datos = archivo.read()
            PILImage.open(io.BytesIO(datos)).verify()
        except Exception:
            return Response(
                {'detail': 'El archivo adjunto no es una imagen válida.'},
                status=status.HTTP_400_BAD_REQUEST)

        # 2) Token de Hugging Face (opcional: solo respaldo de la inferencia local)
        token = os.environ.get('HF_TOKEN', '').strip()

        # 3) Clasificación: modelo ViT en local con ONNX Runtime (gratis),
        #    y si falla, la Inference API de Hugging Face con HF_TOKEN.
        try:
            etiquetas, modelo_usado = clasificar_imagen(datos, token)
        except Exception as error:
            return Response(
                {'detail': explicar_error_hf(error)},
                status=status.HTTP_502_BAD_GATEWAY)

        if not etiquetas:
            return Response(
                {'detail': 'El modelo no devolvió resultados para esta imagen.'},
                status=status.HTTP_502_BAD_GATEWAY)

        # 4) Productos relacionados con la etiqueta principal
        relacionados = productos_relacionados(etiquetas[0]['label'])

        return Response({
            'modelo': modelo_usado,
            'principal': etiquetas[0],
            'etiquetas': etiquetas,
            'productos_relacionados': ProductSerializer(
                relacionados, many=True, context={'request': request}).data,
        })
