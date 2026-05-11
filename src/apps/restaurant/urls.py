from rest_framework import routers
from .api.viewsets import RestaurantViewSet
restaurant_router = routers.DefaultRouter()

restaurant_router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
