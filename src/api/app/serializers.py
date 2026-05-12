from rest_framework import serializers
from apps.restaurant.models import Employee, Restaurant
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework import serializers
from apps.products.models import (
    Bill, Product, Complement, ComplementGroup
)
from apps.restaurant.models import Employee, Restaurant, Table
from apps.financial.models import PaymentMethod
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

class LoginSerializer(serializers.ModelSerializer):
    restaurant_token = serializers.CharField(write_only=True, required=True)
    code = serializers.CharField(write_only=True, required=True)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    restaurant_id = serializers.UUIDField(read_only=True)
    employee_id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Employee
        fields = ['refresh', 'access', 'restaurant_token', 'restaurant_id', 'employee_id', 'name', 'code']
        read_only_fields = ['refresh', 'access', 'restaurant_id', 'employee_id', 'name']

    def create(self, validated_data):
        restaurant_token = validated_data.get('restaurant_token')
        code = validated_data.get('code')
        try:
            restaurant = Restaurant.objects.get(token=restaurant_token)
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError('Usário ou senha incorretos.')
        
        try:
            employee = Employee.objects.get(code=code, is_active=True, is_deleted=False, restaurant=restaurant)
        except Employee.DoesNotExist:
            raise serializers.ValidationError('Usuário ou senha incorretos.')
        
        refresh = RefreshToken.for_user(restaurant.owner)
        refresh['restaurant_id'] = str(restaurant.id)
        refresh['employee_id'] = str(employee.id)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'restaurant_id': str(restaurant.id),
            'employee_id': str(employee.id),
            'name': employee.name,
        }
    
class BillSerializer(serializers.ModelSerializer):
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
        ]

    def create(self, validated_data):
        restaurant_id = self.context['request'].auth.get('restaurant_id')
        employee_id = self.context['request'].auth.get('employee_id')
        validated_data['restaurant_id'] = restaurant_id
        validated_data['opened_by_id'] = employee_id
        return super().create(validated_data)