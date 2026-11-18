from rest_framework.routers import DefaultRouter

from quotes.api.views import QuoteViewSet

router_quotes = DefaultRouter()
# /api/quotes/ · /api/quotes/{id}/ · /api/quotes/{id}/pdf/ · /api/quotes/clients/
router_quotes.register(prefix='quotes', basename='quotes', viewset=QuoteViewSet)
