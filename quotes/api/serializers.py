from django.db import IntegrityError, transaction
from rest_framework import serializers

from products.models import Product
from quotes.models import Quote, QuoteItem
from quotes.pdf import render_quote_pdf


class QuoteItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=16, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteItem
        fields = ['id', 'product', 'code', 'name', 'brand', 'unit', 'unit_price', 'quantity', 'line_total']


class QuoteItemInputSerializer(serializers.Serializer):
    """Lo que envía el front por cada línea: el producto y la cantidad. El precio lo pone el backend."""

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1, max_value=100000)


class QuoteSerializer(serializers.ModelSerializer):
    items = QuoteItemInputSerializer(many=True, write_only=True)
    client_type_label = serializers.CharField(source='get_client_type_display', read_only=True)
    document_label = serializers.CharField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = [
            'id', 'number',
            'client_type', 'client_type_label', 'document_label', 'client_document', 'client_name',
            'client_email', 'client_phone', 'client_address', 'client_contact',
            'subject', 'items', 'labor_description', 'labor_cost',
            'delivery_time', 'payment_terms', 'validity_days', 'notes',
            'products_subtotal', 'subtotal', 'iva_rate', 'iva', 'total',
            'pdf_url', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['number', 'products_subtotal', 'subtotal', 'iva_rate', 'iva', 'total', 'created_at', 'updated_at']
        extra_kwargs = {
            'labor_cost': {'min_value': 0},
            'validity_days': {'min_value': 1, 'max_value': 365},
        }

    def get_created_by_name(self, quote):
        user = quote.created_by
        return (user.get_full_name() or user.username) if user else None

    def get_pdf_url(self, quote):
        if not quote.pk:
            return None
        request = self.context.get('request')
        path = f'/api/quotes/{quote.pk}/pdf/'
        return request.build_absolute_uri(path) if request else path

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['items'] = QuoteItemSerializer(instance.items.all(), many=True).data
        return data

    def validate(self, attrs):
        items = attrs.get('items', None)
        labor = attrs.get('labor_cost', getattr(self.instance, 'labor_cost', 0)) or 0
        if items is not None:
            if not items and labor <= 0:
                raise serializers.ValidationError({'items': 'Agrega al menos un producto o un valor de mano de obra.'})
            ids = [line['product'].pk for line in items]
            if len(ids) != len(set(ids)):
                raise serializers.ValidationError({'items': 'Un producto aparece repetido; ajusta su cantidad en una sola línea.'})
        email = attrs.get('client_email', getattr(self.instance, 'client_email', ''))
        phone = attrs.get('client_phone', getattr(self.instance, 'client_phone', ''))
        if not email and not phone:
            raise serializers.ValidationError({'client_email': 'Indica al menos un correo o un celular del cliente.'})
        return attrs

    def _save_items(self, quote, lines, previous_prices):
        quote.items.all().delete()
        QuoteItem.objects.bulk_create([
            QuoteItem(
                quote=quote, product=line['product'], position=index,
                code=line['product'].code, name=line['product'].name, brand=line['product'].brand,
                unit=line['product'].unit, quantity=line['quantity'],
                # Al editar se respeta el precio con el que ya se había cotizado ese producto.
                unit_price=previous_prices.get(line['product'].pk, line['product'].sale_price),
            )
            for index, line in enumerate(lines)
        ])

    def _finish(self, quote):
        quote.recalculate()
        quote.save()
        render_quote_pdf(quote)
        return quote

    def create(self, validated_data):
        lines = validated_data.pop('items')
        user = self.context['request'].user
        for attempt in range(3):  # el consecutivo es único: si dos usuarios crean a la vez, se reintenta
            try:
                with transaction.atomic():
                    quote = Quote.objects.create(number=Quote.next_number(), created_by=user, **validated_data)
                    self._save_items(quote, lines, {})
                    return self._finish(quote)
            except IntegrityError:
                if attempt == 2:
                    raise
        raise RuntimeError('unreachable')

    def update(self, instance, validated_data):
        lines = validated_data.pop('items', None)
        with transaction.atomic():
            for field, value in validated_data.items():
                setattr(instance, field, value)
            instance.save()
            if lines is not None:
                previous = {item.product_id: item.unit_price for item in instance.items.all() if item.product_id}
                self._save_items(instance, lines, previous)
            return self._finish(instance)
