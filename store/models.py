from django.contrib.auth.models import User
from django.db import models


class Product(models.Model):
    """Producto de la tienda."""

    CATEGORIES = [
        ('celulares', 'Celulares'),
        ('laptops', 'Laptops'),
        ('audifonos', 'Audífonos'),
        ('accesorios', 'Accesorios'),
        ('otros', 'Otros'),
    ]

    name = models.CharField('nombre', max_length=200)
    description = models.TextField('descripción', blank=True)
    price = models.DecimalField('precio', max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField('stock', default=0)
    category = models.CharField('categoría', max_length=50, choices=CATEGORIES, default='otros')
    image = models.ImageField('imagen', upload_to='productos/', blank=True, null=True)
    model_3d_url = models.URLField('modelo 3D', blank=True, max_length=300)
    created_at = models.DateTimeField('creado el', auto_now_add=True)

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Order(models.Model):
    """Pedido hecho por un cliente."""

    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='usuario')
    created_at = models.DateTimeField('creado el', auto_now_add=True)
    status = models.CharField('estado', max_length=20, choices=STATUS_CHOICES, default='pendiente')
    total = models.DecimalField('total', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f'Pedido #{self.pk} - {self.user.username}'


class OrderItem(models.Model):
    """Línea de un pedido: producto + cantidad."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='pedido')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items', verbose_name='producto')
    quantity = models.PositiveIntegerField('cantidad', default=1)
    unit_price = models.DecimalField('precio unitario', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'ítem del pedido'
        verbose_name_plural = 'ítems del pedido'

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
