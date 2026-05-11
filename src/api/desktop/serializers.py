from rest_framework import serializers
from apps.products.models import (
    Product, Complement, ComplementGroup, Order, OrderComplement, Bill, BillGroup
)
from apps.restaurant.models import Employee, Restaurant, Table
from apps.financial.models import Cashier, PaymentMethod, Sale, Transaction
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
class PaymentMethodSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    class Meta:
        model = PaymentMethod
        fields = ['id', 'display_name', 'position', 'method']
class RestaurantSerializer(serializers.ModelSerializer):
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    class Meta:
        model = Restaurant
        fields = '__all__'
class TableSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(source='bills.count', read_only=True)
    class Meta:
        model = Table
        fields = '__all__'
class ComplementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complement
        fields = [
            'id',
            'name',
            'description',
            'price',
            'max',
            'min'
        ]
class ComplementGroupSerializer(serializers.ModelSerializer):
    complements = ComplementSerializer(many=True, read_only=True)
    class Meta:
        model = ComplementGroup
        fields = [
            'id',
            'name',
            'rule',
            'min',
            'max',
            'complements',
        ]


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    printer = serializers.CharField(source='printer.name', read_only=True)
    complement_groups = ComplementGroupSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'price',
            'category',
            'code',
            'sell_type',
            'printer',
            'complement_groups',
        ]

class OrderComplementSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderComplement
        read_only_fields = ['id', 'complement_name']
        fields = [
            'id',
            'complement',
            'complement_name',
            'quantity',
        ]


class CreateOrderSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=True, write_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    complements = serializers.JSONField(write_only=True, required=False)
    class Meta:
        model = Order
        read_only_fields = ['id', 'number', 'launched_by']
        fields = [
            'id',
            'number',
            'bill',
            'product',
            'notes',
            'status',
            'quantity',
            'unit_price',
            'total_price',
            'code',
            'launched_by',
            'product_name',
            'complements',
        ]

    @transaction.atomic
    def create(self, validated_data):
        code = validated_data.pop('code')
        validated_data['restaurant_id'] = validated_data['bill'].restaurant_id
        validated_data['total_price'] = validated_data['quantity'] * validated_data['product'].price
        complements_data = validated_data.pop('complements', [])
        try:
            employee = Employee.objects.get(code=code, is_active=True, is_deleted=False, restaurant_id=validated_data['restaurant_id'])
        except Employee.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Código de funcionário inválido.'})
        validated_data['launched_by_id'] = employee.id
        order = super().create(validated_data)
        created_complements = []
        for complement_data in complements_data:
            complement = OrderComplement.objects.create(
                order=order,
                complement_id=complement_data['complement'],
                quantity=complement_data['quantity']
            )
            created_complements.append(complement)
        complement_grouped_by_complement_group = []
        for complement in created_complements:
            complement_group = complement.complement.complement_group
            existing_group = next((group for group in complement_grouped_by_complement_group if group['complement_group_id'] == complement_group.id), None)
            if existing_group:
                existing_group['complements'].append(complement)
            else:
                complement_grouped_by_complement_group.append({
                    'complement_group_name': complement_group.name,
                    'complement_group_id': complement_group.id,
                    'complements': [complement],
                    'rule': complement_group.rule,
                    'total_price': 0,
                })
        for group in complement_grouped_by_complement_group:
            if group['rule'] == 'HIGH':
                group['total_price'] = max([complement.complement.price for complement in group['complements']])
            elif group['rule'] == 'SUM':
                group['total_price'] = sum([complement.complement.price for complement in group['complements']])
            elif group['rule'] == 'MEDIAN':
                sorted_prices = sorted([complement.complement.price for complement in group['complements']])
                n = len(sorted_prices)
                if n % 2 == 1:
                    group['total_price'] = sorted_prices[n // 2]
                else:
                    group['total_price'] = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2
            group['total_price'] = float(group['total_price'])
            group['complements'] = [{
                'id': str(complement.complement.id),
                'name': complement.complement.name,
                'price': float(complement.complement.price),
                'quantity': complement.quantity,
            } for complement in group['complements']]
            group['complement_group_id'] = str(group['complement_group_id'])
        order.complements_details = complement_grouped_by_complement_group
        order.complements_price = sum([group['total_price'] for group in complement_grouped_by_complement_group])
        order.calculate_total_price()
        order.refresh_from_db()
        return order
    
    def update(self, instance, validated_data):
        if validated_data.get('status') == 'CANCELED':
            code = validated_data.pop('code', None)
            if code:
                try:
                    employee = Employee.objects.get(code=code, is_active=True, is_deleted=False, restaurant_id=instance.restaurant_id)
                    if not employee.can_delete_item:
                        raise serializers.ValidationError({'detail': 'Funcionário não tem permissão para cancelar pedidos.'})
                except Employee.DoesNotExist:
                    raise serializers.ValidationError({'detail': 'Código de funcionário inválido.'})
                instance.canceled_by = employee
                instance.canceled_by_name = employee.name
            if not code:
                raise serializers.ValidationError({'detail': 'Código de funcionário é obrigatório para cancelar um pedido.'})
        return super().update(instance, validated_data)
    
class OrderListSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    launched_by = serializers.CharField(source='launched_by.name', read_only=True)
    canceled_by = serializers.CharField(source='canceled_by.name', read_only=True)
    complements = serializers.JSONField(source='complements_details', read_only=True)
    bill_number = serializers.CharField(source='bill.number', read_only=True)
    class Meta:
        model = Order
        fields = [
            'id',
            'number',
            'product_name',
            'quantity',
            'unit_price',
            'complements_price',
            'total_price',
            'status',
            'notes',
            'launched_by',
            'canceled_by',
            'created',
            'complements',
            'bill_number',
        ]

class BillGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillGroup
        fields = [
            'id',
            'bills',
        ]

    def create(self, validated_data):
        restaurant_id = self.context['request'].auth.get('restaurant_id')
        validated_data['restaurant_id'] = restaurant_id
        return super().create(validated_data)

class BillSerializer(serializers.ModelSerializer):
    code = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = Bill
        fields = [
            'id',
            'number',
            'identification',
            'is_open',
            'opened_by',
            'opened_by_name',
            'table',
            'closed_at',
            'opened_at',
            'code',
        ]

    def create(self, validated_data):
        restaurant_id = self.context['request'].auth.get('restaurant_id')
        validated_data['restaurant_id'] = restaurant_id
        code = validated_data.pop('code')
        try:
            employee = Employee.objects.get(code=code, is_active=True, is_deleted=False, restaurant_id=restaurant_id)
        except Employee.DoesNotExist:
            raise serializers.ValidationError({'detail': 'Código de funcionário inválido.'})
        validated_data['opened_by'] = employee
        return super().create(validated_data)


class BillInGroupDetailSerializer(serializers.ModelSerializer):
    orders = OrderListSerializer(many=True, read_only=True)
    class Meta:
        model = Bill
        fields = [
            'id',
            'number',
            'identification',
            'is_open',
            'orders',
        ]

class BillDetailSerializer(serializers.ModelSerializer):
    orders = OrderListSerializer(many=True, read_only=True)
    table = serializers.CharField(source='table.number', read_only=True)
    bill_group = serializers.SerializerMethodField()
    
    class Meta:
        model = Bill
        fields = [
            'id',
            'number',
            'identification',
            'is_open',
            'opened_by',
            'opened_by_name',
            'table',
            'closed_at',
            'opened_at',
            'orders',
            'bill_group',
            'bill_groups',
        ]

    def get_bill_group(self, obj):
        groups = obj.bill_groups.first()
        if groups:
            bills = groups.bills.filter().prefetch_related(
                Prefetch(
                    'orders',
                    queryset=Order.objects.filter(is_active=True).exclude(status='CANCELED').select_related('product', 'launched_by', 'canceled_by')
                )
            )
            return BillInGroupDetailSerializer(bills, many=True).data
        return None 



class CashierSerializer(serializers.ModelSerializer):
    code = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Cashier
        fields = [
            'id',
            'identification',
            'created',
            'is_open',
            'code',
            'initial_value',
        ]

    @transaction.atomic
    def create(self, validated_data):
        code = validated_data.pop('code', None)
        restaurant_id = self.context['request'].auth.get('restaurant_id')
        validated_data['restaurant_id'] = restaurant_id
        validated_data['is_open'] = True
        if code:
            try:
                employee = Employee.objects.get(code=code, is_active=True, is_deleted=False, restaurant_id=restaurant_id, can_open_cashier=True)
            except Employee.DoesNotExist:
                raise serializers.ValidationError({'detail': 'Código de funcionário inválido.'})
            validated_data['opened_by'] = employee
            validated_data['opened_by_name'] = employee.name
        else:
            raise serializers.ValidationError({'detail': 'Código de funcionário é obrigatório para abrir um caixa.'})
        pm = PaymentMethod.objects.filter(restaurant_id=restaurant_id, method="CASH").first()
        if not pm:
            raise serializers.ValidationError({'detail': 'Método de pagamento em dinheiro não encontrado. Por favor, crie um método de pagamento com tipo "CASH" antes de abrir o caixa.'})
        cashier = super().create(validated_data)
        transaction = Transaction.objects.create(
            cashier=cashier,
            payment_method=pm,
            description='Valor inicial do caixa',
            amount=validated_data['initial_value'],
            status='COMPLETED',
            type="SUPPLY",
            restaurant_id=restaurant_id
        )
        return cashier

    @transaction.atomic
    def update(self, instance, validated_data):
        code = validated_data.pop('code', None)
        if code:
            restaurant_id = self.context['request'].auth.get('restaurant_id')
            try:
                employee = Employee.objects.get(code=code, is_active=True, is_deleted=False, restaurant_id=restaurant_id, can_close_cashier=True)
            except Employee.DoesNotExist:
                raise serializers.ValidationError({'detail': 'Código de funcionário inválido.'})
            instance.closed_by = employee
            instance.closed_by_name = employee.name
        else:
            raise serializers.ValidationError({'detail': 'Código de funcionário é obrigatório para fechar um caixa.'})
        instance.is_open = False
        instance.closed_at = timezone.now()
        instance.final_value = instance.get_current_value()
        instance.save()
        return instance

class CashierDetailSerializer(serializers.ModelSerializer):
    current_value = serializers.CharField(source='get_current_value', read_only=True)
    class Meta:
        model = Cashier
        fields = '__all__'
        read_only_fields = ['id',
            'closed_at',
            'opened_by',
            'opened_by_name',
            'closed_by',
            'closed_by_name',
            'final_value',
            'restaurant',
            'current_value',
        ]


class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='payment_method.display_name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    payment_method_method = serializers.CharField(source='payment_method.method', read_only=True)
    class Meta:
        model = Transaction
        fields = '__all__'