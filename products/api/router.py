from rest_framework.routers import DefaultRouter

from products.api.views import ProductAdminViewSet, ProductPublicViewSet

router_products = DefaultRouter()
# Admin (is_staff): /api/products/  ·  Público (tienda): /api/store/products/
router_products.register(prefix='products', basename='products', viewset=ProductAdminViewSet)
router_products.register(prefix='store/products', basename='store-products', viewset=ProductPublicViewSet)
