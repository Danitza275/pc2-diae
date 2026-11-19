from django.db import transaction
from rest_framework import serializers

from .models import Order, OrderItem, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category',
                  'image', 'model_3d_url', 'created_at']
        read_only_fields = ['id', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    """Solo lectura: muestra el detalle de un pedido ya guardado."""
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price']
        read_only_fields = fields


class ItemInputSerializer(serializers.ModelSerializer):
    """Lo que el cliente envía al crear un pedido."""
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    """Lectura de un pedido (total y precios los puso el servidor)."""
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'user_name', 'status', 'total', 'created_at', 'items']
        read_only_fields = ['id', 'user', 'user_name', 'total', 'created_at', 'items']


class OrderCreateSerializer(serializers.Serializer):
    """Escritura: recibe items (product, quantity) y calcula todo en el servidor."""
    items = ItemInputSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError('El pedido debe tener al menos un producto.')
        for item in items:
            if item['quantity'] < 1:
                raise serializers.ValidationError('La cantidad debe ser al menos 1.')
        return items

    def create(self, validated_data):
        request = self.context['request']
        items = validated_data['items']

        with transaction.atomic():
            # Bloquea las filas para que nadie compre el mismo stock a la vez
            ids = [i['product'].pk for i in items]
            productos = Product.objects.select_for_update().filter(pk__in=ids)
            mapa = {p.pk: p for p in productos}

            # Suma de cantidades por producto (si se repite, se acumulan)
            requerido = {}
            for item in items:
                pk = item['product'].pk
                requerido[pk] = requerido.get(pk, 0) + item['quantity']

            for pk, cantidad in requerido.items():
                if pk not in mapa:
                    raise serializers.ValidationError(f'El producto {pk} no existe.')
                if mapa[pk].stock < cantidad:
                    raise serializers.ValidationError(
                        f'Stock insuficiente para {mapa[pk].name} '
                        f'(disponible: {mapa[pk].stock}, pedido: {cantidad}).')

            order = Order.objects.create(user=request.user, total=0)

            total = 0
            for pk, cantidad in requerido.items():
                producto = mapa[pk]
                OrderItem.objects.create(
                    order=order, product=producto,
                    quantity=cantidad, unit_price=producto.price)
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])
                total += cantidad * producto.price

            order.total = total
            order.save(update_fields=['total'])

        return order
