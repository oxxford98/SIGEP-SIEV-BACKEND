from rest_framework import serializers

from products.models import Product


class ProductAdminSerializer(serializers.ModelSerializer):
    """Todos los campos del inventario, para el panel de administración."""

    margin = serializers.DecimalField(max_digits=7, decimal_places=4, read_only=True)
    inventory_value = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)
    # Con multipart no se puede enviar image=null: este campo permite quitar la imagen.
    remove_image = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'category', 'brand', 'reference', 'unit',
            'stock', 'min_stock', 'unit_cost', 'sale_price', 'margin', 'inventory_value',
            'status', 'location', 'supplier', 'description', 'image', 'remove_image',
            'is_published', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'unit_cost': {'min_value': 0},
            'sale_price': {'min_value': 0},
        }

    def create(self, validated_data):
        validated_data.pop('remove_image', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove = validated_data.pop('remove_image', False)
        replacing = 'image' in validated_data
        if instance.image and (remove or replacing):
            instance.image.delete(save=False)  # no dejar archivos huérfanos en media/
            if not replacing:
                instance.image = None
        return super().update(instance, validated_data)


class ProductPublicSerializer(serializers.ModelSerializer):
    """Vista pública de la tienda: sin costos, proveedor, ubicación ni márgenes."""

    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'category', 'brand', 'reference', 'unit',
            'stock', 'sale_price', 'description', 'image', 'created_at',
        ]
