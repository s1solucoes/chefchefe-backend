from rest_framework import routers
from apps.user.api.viewsets import UserLoginViewSet, UserRestaurantViewSet
user_router = routers.DefaultRouter()

user_router.register(r'login', UserLoginViewSet)
user_router.register(r'restaurant', UserRestaurantViewSet, basename='user-restaurant')
