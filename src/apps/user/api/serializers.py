from apps.user.models import User
from rest_framework import serializers
from apps.restaurant.models import Restaurant, UserRestaurant
from rest_framework_simplejwt.tokens import RefreshToken

class UserLoginSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True, write_only=True)
    restaurant_token = serializers.CharField(write_only=True, required=True)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)
    restaurant_id = serializers.UUIDField(read_only=True)
    class Meta:
        model = User
        fields = ['refresh', 'access', 'email', 'password', 'restaurant_token', 'restaurant_id']

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        restaurant_token = validated_data.get('restaurant_token')

        try:
            restaurant = Restaurant.objects.get(token=restaurant_token)
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError('Usário ou senha incorretos.')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Usuário ou senha incorretos.')

        if not user.check_password(password):
            raise serializers.ValidationError('Usuário ou senha incorretos.')
        
        if not UserRestaurant.objects.filter(user=user, restaurant=restaurant, is_active=True, is_deleted=False).exists():
            raise serializers.ValidationError('Usuário ou senha incorretos.')
        
        refresh = RefreshToken.for_user(user)
        refresh['restaurant_id'] = str(restaurant.id)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'restaurant_id': str(restaurant.id)
        }
