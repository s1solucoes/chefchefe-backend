from .serializers import (
    BillSerializer
)
from rest_framework import viewsets
from apps.products.models import (
    Bill
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class BillViewSet(viewsets.ModelViewSet):
    serializer_class = BillSerializer
    http_method_names = ['get']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.auth is None:
            return Bill.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        queryset = Bill.objects.filter(restaurant_id=restaurant_id).order_by('number')
        return queryset

    def list(self, request, *args, **kwargs):
        paginated = request.query_params.get('paginated', 'true').lower() == 'true'
        if paginated:
            return super().list(request, *args, **kwargs)
        else:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)