from .serializers import (
    RestaurantSerializer,
)
from rest_framework import viewsets
from apps.restaurant.models import (
    Restaurant,
)
from rest_framework.permissions import IsAuthenticated

class RestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = RestaurantSerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # from token
        restaurant_id = self.request.auth
        print(restaurant_id)
        queryset = Restaurant.objects.filter(user_restaurants__user=user)
        return queryset
    