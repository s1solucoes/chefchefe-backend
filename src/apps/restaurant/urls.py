from rest_framework import routers
from apps.restaurant.api.viewsets import PaymentMethodViewSet, EmployeeViewSet, RestaurantViewSet
restaurant_router = routers.DefaultRouter()

restaurant_router.register(r'payment-method', PaymentMethodViewSet)
restaurant_router.register(r'employee', EmployeeViewSet)
restaurant_router.register(r'restaurant', RestaurantViewSet)
