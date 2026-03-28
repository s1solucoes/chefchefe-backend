from rest_framework import routers
from .api.viewsets import RestaurantViewSet, TableViewSet
restaurant_router = routers.DefaultRouter()

restaurant_router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
restaurant_router.register(r'tables', TableViewSet, basename='table')
