from rest_framework.routers import DefaultRouter
from .viewsets import (
    LoginViewSet,
    ProductViewSet,
    TableViewSet,
    BillViewSet
)
router_app = DefaultRouter()
router_app.register(r'login', LoginViewSet, basename='app-login')
router_app.register(r'products', ProductViewSet, basename='desktop-product')
router_app.register(r'tables', TableViewSet, basename='desktop-table')
router_app.register(r'bills', BillViewSet, basename='desktop-bill')
