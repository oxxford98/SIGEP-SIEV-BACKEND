from django.contrib import admin

from products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'brand', 'stock', 'min_stock', 'sale_price', 'status', 'is_published')
    list_filter = ('category', 'brand', 'is_published')
    search_fields = ('code', 'name', 'brand', 'reference')
