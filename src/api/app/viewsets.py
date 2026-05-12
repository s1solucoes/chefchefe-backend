from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from apps.products.models import Bill, Order, Product, Complement, ComplementGroup
from rest_framework.permissions import AllowAny
from django.db import transaction
from django.db.models import Prefetch, Q
from apps.restaurant.models import Table
from .serializers import (
    LoginSerializer,
    ProductSerializer,
    TableSerializer,
    BillSerializer,
    OrdersSerializer
)


class TableViewSet(ModelViewSet):
    serializer_class = TableSerializer
    http_method_names = ['get']

    def get_queryset(self):
        if self.request.auth is None:
            if self.request.user.is_superuser:
                return Table.objects.all()
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

class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['name', 'category', 'is_active', 'code']



class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    http_method_names = ['get']
    pagination_class = None

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return Product.objects.all()
            return Product.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')

        return (
            Product.objects
            .filter(
                restaurant_id=restaurant_id,
                is_active=True
            )
            .select_related('category', 'printer')
            .prefetch_related(
                Prefetch(
                    'complement_groups',
                    queryset=ComplementGroup.objects.filter(is_active=True).prefetch_related(
                        Prefetch(
                            'complements',
                            queryset=Complement.objects.filter(is_active=True)
                        )
                    )
                )
            )
            .order_by('category', 'position', 'name')
        )

class LoginViewSet(ModelViewSet):
    serializer_class = LoginSerializer
    http_method_names = ['post']
    permission_classes = [AllowAny]



class BillFilter(filters.FilterSet):
    number = filters.CharFilter(field_name='number', lookup_expr='exact')
    is_open = filters.BooleanFilter(field_name='is_open')
    free_group = filters.BooleanFilter(method='filter_free_group')
    current_group = filters.BooleanFilter(method='filter_current_group')
    closed_at__gte = filters.DateTimeFilter(method='filter_closed_at__gte')
    class Meta:
        model = Bill
        fields = ['number', 'is_open', 'free_group', 'current_group', 'closed_at__gte']

    def filter_closed_at__gte(self, queryset, name, value):
        if value:
            return queryset.filter(Q(closed_at__gte=value) | Q(closed_at__isnull=True))
        return queryset

    def filter_free_group(self, queryset, name, value):
        group_id = self.request.query_params.get('current_group')
        if value and not group_id:
            return queryset.filter(bill_groups__isnull=True)
        if value and group_id:
            return queryset.filter(Q(bill_groups__isnull=True) | Q(bill_groups__id=group_id))
        return queryset


class BillViewSet(ModelViewSet):
    serializer_class = BillSerializer
    http_method_names = ['get', 'post']
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = BillFilter    

    def get_queryset(self):
        if self.request.auth is None:
            if self.request.user.is_superuser:
                return Bill.objects.all()
            return Bill.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        queryset = Bill.objects.filter(restaurant_id=restaurant_id).order_by('-created')
        return queryset
    
    def create(self, request, *args, **kwargs):
        number = request.data.get('number')
        if number:
            restaurant_id = request.auth.get('restaurant_id')
            if Bill.objects.filter(restaurant_id=restaurant_id, number=number, is_open=True).exists():
                return Response({'detail': 'Já existe uma comanda aberta com esse número.'}, status=400)
        return super().create(request, *args, **kwargs)
    
class CreateOrderViewSet(ViewSet):
    http_method_names = ['post']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        restaurant_id = self.request.auth.get('restaurant_id')
        employee_id = self.request.auth.get('employee_id')
        if not restaurant_id or not employee_id:
            return Response({'detail': 'Autenticação inválida.'}, status=401)
        orders = request.data.get('orders', [])
        if not isinstance(orders, list):
            return Response({'detail': 'O corpo da requisição deve ser uma lista de pedidos.'}, status=400)
        if not orders:
            return Response({'detail': 'Nenhum pedido fornecido.'}, status=400)
        to_create = []
        for order_data in orders:
            to_create.append(Order(
                bill_id=order_data['bill'],
                product_id=order_data['product'],
                notes=order_data['notes'],
                status="DELIVERED",
                quantity=order_data['quantity'],
                total_price=order_data['quantity'] * order_data['unit_price'],
                restaurant_id=restaurant_id,
                launched_by_id=employee_id,
            ))

        # 
        Order.objects.bulk_create(to_create)
        return Response({'detail': 'Pedidos criados com sucesso.'}, status=201)



class OrdersViewSet(ModelViewSet):
    serializer_class = OrdersSerializer
    http_method_names = ['get']
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['bill']

    def get_queryset(self):
        if self.request.auth is None:
            if self.request.user.is_superuser:
                return Order.objects.all()
            return Order.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        queryset = Order.objects.filter(restaurant_id=restaurant_id).select_related('product').order_by('-created')
        return queryset