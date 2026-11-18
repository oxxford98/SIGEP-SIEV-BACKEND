from decimal import Decimal

from django.db import models


class Product(models.Model):
    """Producto del inventario SIEV (campos de la hoja «Inventario SIEV»)."""

    STATUS_OK = 'OK'
    STATUS_RESTOCK = 'Reponer'

    code = models.CharField('código', max_length=30, unique=True)
    name = models.CharField('producto', max_length=200)
    category = models.CharField('categoría', max_length=100, db_index=True)
    brand = models.CharField('marca', max_length=100)
    reference = models.CharField('referencia', max_length=150, blank=True)
    unit = models.CharField('unidad', max_length=50, default='Unidad')
    stock = models.PositiveIntegerField('stock', default=0)
    min_stock = models.PositiveIntegerField('stock mínimo', default=0)
    unit_cost = models.DecimalField('costo unitario', max_digits=14, decimal_places=2, default=0)
    sale_price = models.DecimalField('precio venta', max_digits=14, decimal_places=2, default=0)
    location = models.CharField('ubicación', max_length=150, blank=True)
    supplier = models.CharField('proveedor', max_length=150, blank=True, default='Por definir')
    description = models.TextField('descripción', blank=True)
    image = models.ImageField('imagen', upload_to='products/', blank=True, null=True)
    is_published = models.BooleanField('publicado en tienda', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'producto'
        verbose_name_plural = 'productos'

    def __str__(self):
        return f'{self.code} · {self.name}'

    @property
    def margin(self):
        """Margen sobre el precio de venta: (precio - costo) / precio."""
        if not self.sale_price:
            return Decimal('0')
        return (self.sale_price - self.unit_cost) / self.sale_price

    @property
    def inventory_value(self):
        return self.unit_cost * self.stock

    @property
    def status(self):
        """«Reponer» cuando el stock llega al mínimo (igual que la hoja de inventario)."""
        return self.STATUS_RESTOCK if self.stock <= self.min_stock else self.STATUS_OK
