"""Comando para cargar datos de prueba masivos (seed).

Uso:
    python manage.py seed            # crea datos solo si la tienda está vacía
    python manage.py seed --reset     # borra todo lo de store y lo vuelve a crear
"""
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from store.models import Order, OrderItem, Product

# (nombre, categoría, precio, stock, descripción)
PRODUCTOS = [
    ('SmartPhone X', 'celulares', 1299.00, 15, 'Pantalla de 6.5", 128 GB, doble cámara.'),
    ('SmartPhone X Pro', 'celulares', 1799.00, 8, 'Versión Pro con cámara de 108 MP.'),
    ('Galaxy A15', 'celulares', 899.00, 25, 'Pantalla AMOLED de 6.5", batería 5000 mAh.'),
    ('Redmi Note 13', 'celulares', 749.00, 30, 'Cámara de 108 MP y carga rápida de 33W.'),
    ('iPhone 13', 'celulares', 2499.00, 5, 'Chip A15, pantalla Super Retina XDR.'),
    ('Motorola Edge 40', 'celulares', 1199.00, 12, 'Pantalla curva de 6.5" y resistencia al agua.'),
    ('Laptop UltraBook 14', 'laptops', 3299.00, 6, 'Intel Core i7, 16 GB RAM, SSD 512 GB.'),
    ('Laptop Gamer RTX', 'laptops', 5499.00, 4, 'RTX 4060, 16 GB RAM, pantalla 144 Hz.'),
    ('Notebook Air 13', 'laptops', 2799.00, 10, 'Ultraligera de 1.2 kg, batería 12 h.'),
    ('Laptop Oficina 15', 'laptops', 2199.00, 14, 'Ryzen 5, 8 GB RAM, SSD 256 GB.'),
    ('MacBook Air M2', 'laptops', 5999.00, 3, 'Chip M2, pantalla Liquid Retina.'),
    ('Chromebook Flex', 'laptops', 1499.00, 9, 'Táctil 2 en 1, ideal para estudiar.'),
    ('Audífonos Studio', 'audifonos', 349.00, 40, 'Cancelación de ruido, 20 h de batería.'),
    ('Audífonos Gaming RGB', 'audifonos', 289.00, 35, 'Sonido envolvente 7.1 con micrófono.'),
    ('Earbuds Pro', 'audifonos', 459.00, 28, 'Inalámbricos con cancelación activa.'),
    ('Audífonos Bluetooth Sport', 'audifonos', 199.00, 50, 'Resistentes al sudor, IPX7.'),
    ('Audífonos con Cable', 'audifonos', 89.00, 60, 'Conector USB-C, cable de 1.2 m.'),
    ('Mouse Gamer 16K', 'accesorios', 219.00, 45, 'Sensor 16000 DPI, 8 botones programables.'),
    ('Teclado Mecánico RGB', 'accesorios', 399.00, 22, 'Switches azules, retroiluminación RGB.'),
    ('Mousepad XXL', 'accesorios', 79.00, 55, 'Base antideslizante de 90x40 cm.'),
    ('Webcam Full HD', 'accesorios', 259.00, 18, '1080p con micrófono estéreo.'),
    ('Hub USB-C 6 en 1', 'accesorios', 189.00, 26, 'HDMI, 3 USB, lector SD y PD 100W.'),
    ('Cargador 65W GaN', 'accesorios', 159.00, 33, 'Compacto, carga laptop y celular.'),
    ('SmartWatch Fit', 'accesorios', 549.00, 17, 'Pantalla AMOLED, GPS y oxímetro.'),
    ('Parlante Bluetooth', 'accesorios', 329.00, 24, 'Potencia 20 W, resistente al agua.'),
    ('Disco SSD 1 TB', 'accesorios', 499.00, 20, 'Lectura 550 MB/s, interfaz SATA.'),
    ('Memoria RAM 16 GB', 'accesorios', 379.00, 19, 'DDR4 3200 MHz, para laptop.'),
    ('Impresora Multifunción', 'otros', 899.00, 7, 'Impresión, copia y escaneo WiFi.'),
    ('Tablet 10 pulgadas', 'otros', 1099.00, 11, 'Android, 4 GB RAM, 128 GB.'),
    ('Consola Retro', 'otros', 649.00, 13, '800 juegos clásicos preinstalados.'),
]

# (nombre, categoría, precio, stock, descripción)
COLORS = {
    'celulares': (36, 99, 235),
    'laptops': (22, 163, 74),
    'audifonos': (147, 51, 234),
    'accesorios': (234, 88, 12),
    'otros': (71, 85, 105),
}

MODELOS_3D = [
    'https://modelviewer.dev/shared-assets/models/Astronaut.glb',
    'https://modelviewer.dev/shared-assets/models/RobotExpressive.glb',
    'https://modelviewer.dev/shared-assets/models/glTF-Sample-Models/2.0/BoomBox/glTF-Binary/BoomBox.glb',
]


class Command(BaseCommand):
    help = 'Carga datos de prueba masivos: usuarios, productos, pedidos e ítems.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Borra los datos de store antes de crearlos.')

    def handle(self, *args, **options):
        random.seed(42)  # datos siempre iguales (reproducibles)

        if options['reset']:
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            User.objects.filter(username__startswith='cliente').delete()
            self.stdout.write('Datos anteriores eliminados.')

        if Product.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Ya hay datos. Usa --reset para volver a crearlos.'))
            return

        self.crear_usuarios()
        self.crear_productos()
        self.crear_pedidos()

        self.stdout.write(self.style.SUCCESS(
            f'OK -> {User.objects.count()} usuarios, {Product.objects.count()} productos, '
            f'{Order.objects.count()} pedidos, {OrderItem.objects.count()} ítems.'))

    def crear_usuarios(self):
        for i in range(1, 11):
            username = f'cliente{i}'
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, email=f'{username}@correo.com',
                    password='cliente123',
                    first_name=f'Cliente {i}', last_name='Prueba')
        self.stdout.write('10 clientes creados (contraseña: cliente123).')

    def crear_productos(self):
        ahora = timezone.now()
        for i, (nombre, cat, precio, stock, desc) in enumerate(PRODUCTOS):
            p = Product.objects.create(
                name=nombre, description=desc, price=precio, stock=stock,
                category=cat, image=self.crear_imagen(nombre, cat, i),
                model_3d_url=random.choice(MODELOS_3D) if i % 5 == 0 else '')
            # antigüedad de 1 a 90 días
            Product.objects.filter(pk=p.pk).update(
                created_at=ahora - timedelta(days=random.randint(1, 90)))
        self.stdout.write(f'{len(PRODUCTOS)} productos creados con imagen.')

    def crear_imagen(self, nombre, cat, i):
        """Genera una imagen PNG simple para el producto."""
        color = COLORS[cat]
        img = Image.new('RGB', (600, 600), color)
        draw = ImageDraw.Draw(img)
        try:
            grande = ImageFont.load_default(size=54)
            chico = ImageFont.load_default(size=30)
        except TypeError:  # Pillow viejo
            grande = ImageFont.load_default()
            chico = ImageFont.load_default()

        draw.rectangle([0, 430, 600, 600], fill=(15, 15, 20))
        draw.text((30, 30), cat.upper(), font=chico, fill=(255, 255, 255))

        # nombre del producto en 2 líneas
        palabras, lineas, actual = nombre.split(), [], ''
        for p in palabras:
            if len(actual + ' ' + p) > 16:
                lineas.append(actual)
                actual = p
            else:
                actual = (actual + ' ' + p).strip()
        lineas.append(actual)
        y = 455 if len(lineas) > 1 else 485
        for linea in lineas[:2]:
            draw.text((30, y), linea, font=grande, fill=(255, 255, 255))
            y += 60

        ruta = f'productos/seed_{i:02d}.png'
        img.save(f'media/{ruta}')
        return ruta

    def crear_pedidos(self):
        ahora = timezone.now()
        productos = list(Product.objects.all())
        clientes = list(User.objects.filter(username__startswith='cliente'))
        estados = ['pendiente', 'enviado', 'entregado']
        pesos = [4, 3, 3]

        for i in range(40):
            cliente = random.choice(clientes)
            pedido = Order.objects.create(user=cliente, total=0)
            total = 0
            for _ in range(random.randint(1, 4)):
                prod = random.choice(productos)
                cantidad = random.randint(1, 3)
                OrderItem.objects.create(
                    order=pedido, product=prod, quantity=cantidad,
                    unit_price=prod.price)
                total += cantidad * prod.price
            pedido.total = total
            pedido.status = random.choices(estados, weights=pesos)[0]
            pedido.save(update_fields=['total', 'status'])
            # antigüedad de 0 a 60 días
            Order.objects.filter(pk=pedido.pk).update(
                created_at=ahora - timedelta(days=random.randint(0, 60),
                                             hours=random.randint(0, 23)))
        self.stdout.write('40 pedidos creados con sus ítems.')
