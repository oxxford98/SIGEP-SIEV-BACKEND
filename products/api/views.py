from django.db.models import Q
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from products.api.serializers import ProductAdminSerializer, ProductPublicSerializer
from products.models import Product


def filter_products(queryset, params):
    """?search= busca en código, nombre, marca y referencia; ?category= filtra exacto."""
    q = params.get('search', '').strip()
    if q:
        queryset = queryset.filter(
            Q(code__icontains=q) | Q(name__icontains=q) | Q(brand__icontains=q) | Q(reference__icontains=q)
        )
    category = params.get('category', '').strip()
    if category:
        queryset = queryset.filter(category=category)
    return queryset


class ProductAdminViewSet(ModelViewSet):
    """CRUD de productos. Solo personal (is_staff) hasta que existan roles."""

    serializer_class = ProductAdminSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return filter_products(Product.objects.all(), self.request.query_params)

    def perform_destroy(self, instance):
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()


class ProductPublicViewSet(ReadOnlyModelViewSet):
    """Catálogo público de la tienda: solo productos publicados."""

    serializer_class = ProductPublicSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def get_queryset(self):
        return filter_products(Product.objects.filter(is_published=True), self.request.query_params)
