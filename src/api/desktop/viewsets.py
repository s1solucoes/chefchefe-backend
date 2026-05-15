from rest_framework.viewsets import ModelViewSet, ViewSet
from apps.products.models import Category, Product, ComplementGroup, Complement, Order, Bill, BillGroup
from apps.restaurant.models import PrintJob, Printer, Restaurant, Table
from .serializers import CashierDetailSerializer, PrintJobSerializer, ProductSerializer, CreateOrderSerializer, BillSerializer, BillDetailSerializer, RestaurantSerializer, TableSerializer, BillGroupSerializer, CashierSerializer, PaymentMethodSerializer, SaleSerializer, TransactionSerializer
from django_filters import rest_framework as filters
from apps.financial.models import Cashier, PaymentMethod, Transaction, Sale
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch, Q, Sum, Avg, Count, F
from rest_framework.response import Response
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from django.utils.text import slugify
class TableViewSet(ModelViewSet):
    serializer_class = TableSerializer
    http_method_names = ['get']

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



class CreateOrderViewSet(ModelViewSet):
    serializer_class = CreateOrderSerializer
    http_method_names = ['post', 'patch']

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return Order.objects.all()
            return Order.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        return Order.objects.filter(restaurant_id=restaurant_id)
    
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
    http_method_names = ['get', 'post', 'patch']
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = BillFilter

    def create(self, request, *args, **kwargs):
        number = request.data.get('number')
        if number:
            restaurant_id = request.auth.get('restaurant_id')
            if Bill.objects.filter(restaurant_id=restaurant_id, number=number, is_open=True).exists():
                return Response({'detail': 'Já existe uma comanda aberta com esse número.'}, status=400)
        return super().create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BillDetailSerializer
        return BillSerializer
    
    def retrieve(self, request, *args, **kwargs):
        qs = self.get_queryset().prefetch_related(
            Prefetch(
                'orders',
                queryset=Order.objects.filter(is_active=True).exclude(status='CANCELED').select_related('product', 'launched_by', 'canceled_by')
            )
        )
        bill = qs.get(pk=kwargs['pk'])
        serializer = self.get_serializer(bill)
        return Response(serializer.data)

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return Bill.objects.all()
            return Bill.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        return  Bill.objects.filter(
                restaurant_id=restaurant_id,
                is_active=True,
                is_deleted=False
            ).order_by('number')
    

class RestaurantViewSet(ModelViewSet):
    serializer_class = RestaurantSerializer
    http_method_names = ['get']

    def get_queryset(self):
        user = self.request.user
        restaurant_id = self.request.auth.get('restaurant_id')
        queryset = Restaurant.objects.filter(user_restaurants__user=user, id=restaurant_id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        restaurant_id = request.auth.get('restaurant_id')
        if restaurant_id:
            queryset = self.get_queryset().get(id=restaurant_id)
            serializer = self.get_serializer(queryset)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Restaurant não encontrado.'}, status=404)

class BillGroupViewSet(ModelViewSet):
    serializer_class = BillGroupSerializer
    http_method_names = ['post']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        restaurant_id = request.auth.get('restaurant_id')
        bills = request.data.get('bills', [])
        group_id = request.data.get('group_id', None)
        if group_id:
            print(f'Atualizando grupo {group_id} com as contas: {bills}')
            try:
                group = BillGroup.objects.get(id=group_id, restaurant_id=restaurant_id)
                if len(bills) <= 1:
                    group.delete()
                    return Response({'detail': 'Grupo de contas deletado, pois possui menos de 2 contas.'}, status=200)
                group.bills.set(bills)
                group.save()
            except BillGroup.DoesNotExist:
                return Response({'detail': 'Grupo de contas não encontrado.'}, status=404)
        elif len(bills) > 1:
            return super().create(request, *args, **kwargs)
        else:
            return Response({'detail': 'É necessário fornecer pelo menos 2 contas para criar um grupo.'}, status=400)
        serializer = self.get_serializer(group)
        return Response(serializer.data)


class CashierViewSet(ModelViewSet):
    serializer_class = CashierSerializer
    queryset = Cashier.objects.all()
    http_method_names = ['get', 'post', 'patch']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_open']

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return Cashier.objects.all()
            return Cashier.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        return Cashier.objects.filter(restaurant_id=restaurant_id)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CashierSerializer
        if self.action == 'retrieve':
            return CashierDetailSerializer
        if self.action == 'partial_update':
            return CashierSerializer
        return CashierSerializer
    
    def list(self, request, *args, **kwargs):
        paginated = request.query_params.get('paginated', 'true').lower() == 'true'
        if paginated:
            return super().list(request, *args, **kwargs)
        else:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
    

class PaymentMethodViewSet(ModelViewSet):
    serializer_class = PaymentMethodSerializer
    queryset = PaymentMethod.objects.all()
    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return PaymentMethod.objects.all()
            return PaymentMethod.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        return PaymentMethod.objects.filter(restaurant_id=restaurant_id)
    

class PaymentMethodsStatsViewSet(ViewSet):
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        restaurant_id = request.auth.get('restaurant_id')
        cashier_id = request.query_params.get('cashier_id')
        queryset = Transaction.objects.filter(restaurant_id=restaurant_id, status='COMPLETED').select_related('payment_method')
        if cashier_id:
            queryset = queryset.filter(cashier_id=cashier_id)

        total_transactions = queryset.count()

        stats = queryset.values('payment_method_id').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id'),
            payment_method_name=F('payment_method__description'),
            method_type=F('payment_method__method')
        ).order_by('-total_amount')

        return Response({
            'total_transactions': total_transactions,
            'payment_method_stats': stats
        })
    
class FinishBillsViewSet(ViewSet):
    http_method_names = ['post']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        restaurant_id = request.auth.get('restaurant_id')
        bill_ids = request.data.get('bills', [])
        payments = request.data.get('payments', [])
        cashier_id = request.data.get('cashier')
        tip_value = request.data.get('tip_value', 0)
        tip_percentage = request.data.get('tip_percentage', 0)
        total_received = request.data.get('total_received', 0)
        total = request.data.get('total', 0)
        subtotal = request.data.get('subtotal', 0)
        discount = request.data.get('discount', 0)
        exchange = request.data.get('change', 0)

        if not bill_ids:
            return Response({'detail': 'Nenhuma comanda fornecida.'}, status=400)
        bills = Bill.objects.filter(id__in=bill_ids, restaurant_id=restaurant_id, is_open=True).prefetch_related('orders__product')
        if bills.count() != len(bill_ids):
            return Response({'detail': 'Algumas comandas não foram encontradas ou já estão fechadas.'}, status=404)
        
        cashier = Cashier.objects.filter(id=cashier_id, restaurant_id=restaurant_id, is_open=True).first()
        if not cashier:
            return Response({'detail': 'Caixa não encontrado.'}, status=404)
        

        sale = Sale.objects.create(
            cashier=cashier,
            status='COMPLETED',
            subtotal=subtotal,
            discount=discount,
            exchange=exchange,
            received=total_received,
            tip_value=tip_value,
            tip_percentage=tip_percentage,
            total=total,
            balance=total_received - exchange,
            restaurant_id=restaurant_id
        )
        
        for payment in payments:
            payment_method_id = payment.get('method')
            amount = payment.get('amount')
            if not payment_method_id or amount is None:
                 return Response({'detail': 'Dados de pagamento incompletos.'}, status=400)
            tx = Transaction.objects.create(
                sale=sale,
                cashier=cashier,
                payment_method_id=payment_method_id,
                amount=amount,
                type='SALE',
                status='COMPLETED',
                description=f'Pagamento recebido de comanda',
                restaurant_id=restaurant_id
            )
        
        if exchange > 0:
            exmid = request.data.get('change_method')
            exchange_method = None
            if not exmid:
                exchange_method = PaymentMethod.objects.filter(restaurant_id=restaurant_id, method='CASH').first()
            else:
                exchange_method = PaymentMethod.objects.filter(id=exmid, restaurant_id=restaurant_id).first()
            Transaction.objects.create(
                sale=sale,
                cashier=cashier,
                amount=-exchange,
                payment_method=exchange_method,
                type='EXCHANGE',
                status='COMPLETED',
                description='Troco devolvido ao cliente',
                restaurant_id=restaurant_id
            )
            

        for bill in bills:
            bill.is_open = False
            bill.sale = sale
            bill.save()
        return Response({'detail': 'Contas finalizadas com sucesso.'}, status=200)
    

class SaleViewSet(ModelViewSet):
    serializer_class = SaleSerializer
    queryset = Sale.objects.all()
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cashier']

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return Sale.objects.all()
            return Sale.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        return Sale.objects.filter(restaurant_id=restaurant_id).order_by('-created')
    
class Pagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
class TransactionViewSet(ModelViewSet):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sale', 'cashier']
    pagination_class = Pagination

    def get_queryset(self):
        if not self.request.auth:
            if self.request.user.is_superuser:
                return Transaction.objects.all()
            return Transaction.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        return Transaction.objects.filter(restaurant_id=restaurant_id).order_by('-created')
    

class PrintJobViewSet(ModelViewSet):
    serializer_class = PrintJobSerializer
    http_method_names = ['get', 'patch']
    pagination_class = None

    def get_queryset(self):
        if self.request.auth is None:
            if self.request.user.is_superuser:
                return PrintJob.objects.all()
            return PrintJob.objects.none()
        restaurant_id = self.request.auth.get('restaurant_id')
        queryset = PrintJob.objects.filter(restaurant_id=restaurant_id).select_related('printer').order_by('created')
        return queryset
    
    def list(self, request, *args, **kwargs):
        first = self.get_queryset().filter(status='PENDING').order_by('created').first()
        if first:
            serializer = self.get_serializer(first)
            return Response({
                'found': True,
                'print_job': serializer.data
            })
        else:
            return Response({
                'found': False,
                'print_job': None
            }, status=200)



class ImportProductsViewSet(ViewSet):
    http_method_names = ['post']
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        token = request.query_params.get('token')
        products_data = request.data
        # name, category, description, price, code, sell_type, position, printer
        restaurant = Restaurant.objects.filter(token=token).first()
        for product_data in products_data:
            category, _ = Category.objects.get_or_create(name=product_data.get('category'), restaurant=restaurant)
            printer, _ = Printer.objects.get_or_create(name=product_data.get('printer'), restaurant=restaurant)
            product, created = Product.objects.update_or_create(
                slug=slugify(product_data.get('name')),
                restaurant=restaurant,
                defaults={
                    "name": product_data.get('name'),
                    "category": category,
                    "description": product_data.get('description'),
                    "price": product_data.get('price'),
                    "code": product_data.get('code'),
                    "sell_type": product_data.get('sell_type', 'UN'),
                    "position": product_data.get('position', 0),
                    "printer": printer
                }
            )
        return Response({'detail': 'Produtos importados com sucesso.'}, status=200)


class CashierStats(ViewSet):
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        cashier_id = request.query_params.get('cashier_id')
        closed_bills_ = Bill.objects.filter(
            is_open=False,
            sale__isnull=True,
        ).update(cashier_id=cashier_id)

        bills = Bill.objects.filter(
            Q(sale__cashier_id=cashier_id),
            is_open=False,
        ).select_related('sale')

        closed_bills = Bill.objects.filter(
            is_open=False,
            cashier_id=cashier_id, 
            sale__isnull=True
        ).select_related('sale')

        orders_stats = Order.objects.filter(
            bill__in=bills,
        ).exclude(status='CANCELED').values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_revenue')

        canceled_orders = Order.objects.filter(
            bill__in=bills,
            status='CANCELED'
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_revenue')

        payment_methods = Transaction.objects.filter(
            sale__cashier_id=cashier_id,
            type='SALE',
            status='COMPLETED'
        ).values('payment_method__method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        payment_methods_exchange = Transaction.objects.filter(
            sale__cashier_id=cashier_id,
            type='EXCHANGE',
            status='COMPLETED'
        ).values('payment_method__method').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')

        final_methods = []
        for method in payment_methods:
            data = {
                'method': method['payment_method__method'],
                'total_amount': method['total_amount'],
                'transaction_count': method['transaction_count'],
                'exchange_amount': payment_methods_exchange.filter(payment_method__method=method['payment_method__method']).aggregate(total_exchange=Sum('amount'))['total_exchange'] or 0
            }
            data['net_amount'] = data['total_amount'] + data['exchange_amount']
            final_methods.append(data)

        return Response({
            'bills_count': bills.count(),
            'closed_bills_count': closed_bills.count(),
            'total_revenue': bills.aggregate(total_revenue=Sum('sale__balance'))['total_revenue'] or 0,
            'orders_stats': orders_stats,
            'canceled_orders': canceled_orders,
            'payment_methods': payment_methods,
            'payment_methods_exchange': payment_methods_exchange,
            'final_methods': final_methods
        })