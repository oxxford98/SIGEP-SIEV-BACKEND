from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

# Los PDF tienen datos de clientes: se guardan fuera de MEDIA_ROOT (que se sirve
# públicamente en desarrollo) y solo se descargan por el endpoint autenticado.
private_storage = FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)

IVA_RATE = Decimal('0.19')
CENT = Decimal('0.01')


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


class Quote(models.Model):
    """Cotización de un servicio para un cliente (persona natural o jurídica)."""

    NATURAL = 'natural'
    LEGAL = 'juridica'
    CLIENT_TYPES = [(NATURAL, 'Persona natural'), (LEGAL, 'Persona jurídica')]

    number = models.CharField('número', max_length=20, unique=True, editable=False)

    # Datos del cliente guardados en la cotización (todavía no hay directorio de clientes).
    client_type = models.CharField('tipo de cliente', max_length=10, choices=CLIENT_TYPES, default=NATURAL)
    client_document = models.CharField('identificación / NIT', max_length=30)
    client_name = models.CharField('nombre o razón social', max_length=200)
    client_email = models.EmailField('correo', blank=True)
    client_phone = models.CharField('celular', max_length=30, blank=True)
    client_address = models.CharField('dirección', max_length=200, blank=True)
    client_contact = models.CharField('persona de contacto', max_length=150, blank=True)

    subject = models.CharField('asunto', max_length=255)
    labor_description = models.CharField('descripción de la mano de obra', max_length=255, blank=True)
    labor_cost = models.DecimalField('mano de obra', max_digits=14, decimal_places=2, default=0)
    delivery_time = models.CharField('tiempo de entrega', max_length=120)
    payment_terms = models.CharField('tiempo de pago', max_length=120)
    validity_days = models.PositiveIntegerField('validez (días)', default=30)
    notes = models.TextField('observaciones', blank=True)

    # Totales calculados al guardar (recalculate) para no depender de precios futuros.
    products_subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    iva_rate = models.DecimalField(max_digits=5, decimal_places=4, default=IVA_RATE)
    iva = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    pdf = models.FileField(storage=private_storage, upload_to='quotes/', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='quotes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'cotización'
        verbose_name_plural = 'cotizaciones'

    def __str__(self):
        return f'{self.number} · {self.client_name}'

    @property
    def document_label(self):
        return 'NIT' if self.client_type == self.LEGAL else 'Identificación'

    @classmethod
    def next_number(cls):
        """COT-2026-0001, consecutivo por año."""
        prefix = f'COT-{timezone.localdate().year}-'
        last = cls.objects.filter(number__startswith=prefix).order_by('-number').values_list('number', flat=True).first()
        sequence = int(last.rsplit('-', 1)[1]) + 1 if last else 1
        return f'{prefix}{sequence:04d}'

    def recalculate(self):
        self.products_subtotal = money(sum((item.line_total for item in self.items.all()), Decimal('0')))
        self.subtotal = money(self.products_subtotal + Decimal(self.labor_cost))
        self.iva = money(self.subtotal * Decimal(self.iva_rate))
        self.total = money(self.subtotal + self.iva)


class QuoteItem(models.Model):
    """Línea de la cotización. Copia código, nombre y precio del producto al momento de cotizar."""

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='quote_items')
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']

    @property
    def line_total(self):
        return money(self.unit_price * self.quantity)
