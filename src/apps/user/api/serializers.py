from apps.user.models import User
from rest_framework import serializers

class UserLoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True)
    restaurants = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name', 'restaurants', 'id')
        read_only_fields = ('restaurants', 'first_name', 'last_name', 'id')

    def get_restaurants(self, obj):
        user_restaurants = obj.user_restaurants.filter(is_active=True, restaurant__is_active=True)
        data = []
        for user_r in user_restaurants:
            data.append({
                'name': user_r.restaurant.name,
                'id': user_r.restaurant.id,
                'role': user_r.role,
                'permissions': user_r.permission.all().values('permission', 'method'),
                'logo': user_r.restaurant.logo.url if user_r.restaurant.logo else None
            })
        return data
        