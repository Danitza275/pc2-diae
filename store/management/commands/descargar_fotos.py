"""Descarga fotos genéricas de internet (Wikimedia Commons, licencias libres)
y las guarda como imagen de cada producto.

Uso:
    python manage.py descargar_fotos
"""
import io
import json
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image

from store.models import Product

API = 'https://commons.wikimedia.org/w/api.php'
AGENTE = 'SmartTechStore/1.0 (practica universitaria)'

# Palabras clave por categoría (se usan si el nombre no da resultado)
POR_CATEGORIA = {
    'celulares': ['smartphone', 'mobile phone'],
    'laptops': ['laptop computer', 'notebook computer'],
    'audifonos': ['headphones', 'earphones'],
    'accesorios': ['computer keyboard', 'computer mouse'],
    'otros': ['tablet computer', 'electronic device'],
}

# Si el nombre contiene la palabra, se busca también este término
POR_PALABRA = [
    ('mouse', 'computer mouse'), ('teclado', 'computer keyboard'),
    ('webcam', 'webcam'), ('cargador', 'USB charger'),
    ('disco', 'solid state drive'), ('memoria', 'RAM memory module'),
    ('impresora', 'inkjet printer'), ('tablet', 'tablet computer'),
    ('consola', 'video game console'), ('parlante', 'bluetooth speaker'),
    ('watch', 'smartwatch'), ('hub', 'USB hub'),
    ('audifono', 'headphones'), ('earbuds', 'in-ear headphones'),
    ('macbook', 'macbook'), ('chromebook', 'chromebook'),
    ('gaming', 'gaming laptop'), ('ultrabook', 'ultrabook'),
    ('notebook', 'laptop'), ('laptop', 'laptop'),
    ('phone', 'smartphone'), ('smartphone', 'smartphone'),
]

# Títulos que no sirven aunque la palabra aparezca (falsos positivos)
EXCLUIR = ['food', 'biscuit', 'cycling', 'bicycle', 'amsterdam', 'service']


class Command(BaseCommand):
    help = 'Descarga fotos genéricas de internet para los productos.'

    def handle(self, *args, **options):
        productos = list(Product.objects.all())
        if not productos:
            self.stdout.write(self.style.ERROR('No hay productos. Ejecuta primero: python manage.py seed'))
            return

        for producto in productos:
            url, titulo = self.buscar_imagen(producto)
            if not url:
                self.stdout.write(self.style.WARNING(f'  sin foto: {producto.name}'))
                continue
            try:
                datos = self.normalizar(self.descargar(url))
                nombre = f'{slugify(producto.name)}-{producto.pk}.jpg'
                producto.image.save(nombre, ContentFile(datos), save=True)
                self.stdout.write(f'  ok: {producto.name}  <-  {titulo}')
            except Exception as error:
                self.stdout.write(self.style.ERROR(f'  error: {producto.name} ({error})'))

        self.borrar_huerfanos()
        con_foto = Product.objects.exclude(image='').count()
        self.stdout.write(self.style.SUCCESS(
            f'Listo. Productos con foto: {con_foto}/{Product.objects.count()}'))

    def normalizar(self, datos):
        """Convierte lo descargado en un JPEG de máximo 900 px."""
        imagen = Image.open(io.BytesIO(datos)).convert('RGB')
        imagen.thumbnail((900, 900))
        salida = io.BytesIO()
        imagen.save(salida, format='JPEG', quality=85)
        return salida.getvalue()

    # ---------- red ----------

    def buscar_imagen(self, producto):
        for consulta in self.consultas(producto):
            resultado = self.buscar_en_commons(consulta)
            if resultado[0]:
                return resultado
        return None, None

    def consultas(self, producto):
        consultas = []
        nombre = producto.name.lower()
        for palabra, termino in POR_PALABRA:
            if palabra in nombre:
                consultas.append(termino)
        consultas += POR_CATEGORIA.get(producto.category, ['electronics'])
        return consultas

    def buscar_en_commons(self, consulta):
        parametros = urllib.parse.urlencode({
            'action': 'query', 'format': 'json', 'generator': 'search',
            'gsrsearch': f'filetype:bitmap {consulta}',
            'gsrnamespace': 6, 'gsrlimit': 8,
            'prop': 'imageinfo', 'iiprop': 'url|mime', 'iiurlwidth': 900,
        })
        try:
            datos = self.json(f'{API}?{parametros}')
        except Exception:
            return None
        for pagina in datos.get('query', {}).get('pages', {}).values():
            info = (pagina.get('imageinfo') or [{}])[0]
            titulo = pagina.get('title', consulta).lower()
            if any(malo in titulo for malo in EXCLUIR):
                continue
            if info.get('mime') in ('image/jpeg', 'image/png') and info.get('thumburl'):
                return info['thumburl'], pagina.get('title', consulta)
        return None, None

    def descargar(self, url):
        solicitud = urllib.request.Request(url, headers={'User-Agent': AGENTE})
        with urllib.request.urlopen(solicitud, timeout=30) as respuesta:
            return respuesta.read()

    def json(self, url):
        solicitud = urllib.request.Request(url, headers={'User-Agent': AGENTE})
        with urllib.request.urlopen(solicitud, timeout=30) as respuesta:
            return json.loads(respuesta.read().decode('utf-8'))

    # ---------- limpieza ----------

    def borrar_huerfanos(self):
        """Borra las imágenes que ya no usa ningún producto (las del seed)."""
        import os
        from django.conf import settings
        usadas = {p.image.name for p in Product.objects.exclude(image='') if p.image}
        carpeta = settings.MEDIA_ROOT / 'productos'
        if not carpeta.exists():
            return
        for archivo in os.listdir(carpeta):
            if f'productos/{archivo}' not in usadas:
                os.remove(carpeta / archivo)
