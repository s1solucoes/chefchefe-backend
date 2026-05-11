from rest_framework import serializers
from apps.restaurant.models import Restaurant

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'

