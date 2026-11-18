from django.contrib import admin

from quotes.models import Quote, QuoteItem


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 0


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('number', 'client_name', 'client_document', 'subject', 'total', 'created_by', 'created_at')
    search_fields = ('number', 'client_name', 'client_document', 'subject')
    readonly_fields = ('number', 'products_subtotal', 'subtotal', 'iva', 'total', 'pdf')
    inlines = [QuoteItemInline]
