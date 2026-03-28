from rest_framework import serializers
from apps.restaurant.models import Restaurant, Table

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'


class TableSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(source='bills.count', read_only=True)
    class Meta:
        model = Table
        fields = '__all__'
