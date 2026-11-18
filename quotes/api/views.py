from django.db.models import Q
from django.http import FileResponse
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from quotes.api.serializers import QuoteSerializer
from quotes.models import Quote
from quotes.pdf import render_quote_pdf

CLIENT_FIELDS = ['client_type', 'client_document', 'client_name', 'client_email', 'client_phone', 'client_address', 'client_contact']


class QuoteViewSet(ModelViewSet):
    """CRUD de cotizaciones (solo personal). Crear o editar regenera el PDF."""

    serializer_class = QuoteSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = Quote.objects.select_related('created_by').prefetch_related('items')
        q = self.request.query_params.get('search', '').strip()
        if q:
            queryset = queryset.filter(
                Q(number__icontains=q) | Q(client_name__icontains=q) | Q(client_document__icontains=q) | Q(subject__icontains=q)
            )
        return queryset

    def perform_destroy(self, instance):
        if instance.pdf:
            instance.pdf.delete(save=False)
        instance.delete()

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Descarga autenticada del PDF (no está en la carpeta pública de media)."""
        quote = self.get_object()
        if not quote.pdf or not quote.pdf.storage.exists(quote.pdf.name):
            render_quote_pdf(quote)
        download = request.query_params.get('download') == '1'
        return FileResponse(quote.pdf.open('rb'), content_type='application/pdf', as_attachment=download, filename=f'{quote.number}.pdf')

    @action(detail=False, methods=['get'])
    def clients(self, request):
        """Clientes ya cotizados (más reciente primero, sin repetir documento) para reutilizar sus datos."""
        q = request.query_params.get('search', '').strip()
        queryset = Quote.objects.order_by('-created_at')
        if q:
            queryset = queryset.filter(Q(client_name__icontains=q) | Q(client_document__icontains=q) | Q(client_email__icontains=q))
        seen, clients = set(), []
        for row in queryset.values(*CLIENT_FIELDS, 'created_at')[:500]:
            key = (row['client_type'], row['client_document'].strip().lower())
            if key in seen:
                continue
            seen.add(key)
            row['last_quote_at'] = row.pop('created_at')
            clients.append(row)
            if len(clients) == 20:
                break
        return Response(clients)
