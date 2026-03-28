from rest_framework import routers
from .api.viewsets import BillViewSet
bill_router = routers.DefaultRouter()

bill_router.register(r'bills', BillViewSet, basename='bill')
