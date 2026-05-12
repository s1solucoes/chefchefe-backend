from rest_framework.routers import DefaultRouter
from .viewsets import (
    LoginViewSet,
    ProductViewSet,
    TableViewSet,
    BillViewSet,
    CreateOrderViewSet
)
router_app = DefaultRouter()
router_app.register(r'login', LoginViewSet, basename='app-login')
router_app.register(r'products', ProductViewSet, basename='app-product')
router_app.register(r'tables', TableViewSet, basename='app-table')
router_app.register(r'bills', BillViewSet, basename='app-bill')
router_app.register(r'create-order', CreateOrderViewSet, basename='app-create-order')
