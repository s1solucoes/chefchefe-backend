from .serializers import (
    RestaurantSerializer,
    TableSerializer    
)
from rest_framework import viewsets
from apps.restaurant.models import (
    Restaurant,
    Table
)
from rest_framework.response import Response
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
    


class TableViewSet(viewsets.ModelViewSet):
    serializer_class = TableSerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.auth is None:
            return Table.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        queryset = Table.objects.filter(restaurant_id=restaurant_id).order_by('number')
        return queryset

    def list(self, request, *args, **kwargs):
        paginated = request.query_params.get('paginated', 'true').lower() == 'true'
        if paginated:
            return super().list(request, *args, **kwargs)
        else:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)