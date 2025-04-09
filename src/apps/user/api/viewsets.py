from .serializers import UserLoginSerializer
from rest_framework import viewsets
from apps.user.models import User
from rest_framework.response import Response

from django.utils.translation import gettext_lazy as _

class UserLoginViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserLoginSerializer

    def create(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        print('email:', email)

        if not email or not password:
            return Response({'detail': _('Please provide both username and password')}, status=400)

        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({'detail': _('Invalid Credentials')}, status=400)
            serializer = UserLoginSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'detail': _('Invalid Credentials')}, status=400)
        

class UserRestaurantViewSet(viewsets.ViewSet):
    queryset = User.objects.all()
    serializer_class = UserLoginSerializer

    def list(self, request):
        user_id = request.GET.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'detail': _('User not found')}, status=404)
        serializer = UserLoginSerializer(user)
        return Response(serializer.data)