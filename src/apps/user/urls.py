from rest_framework import routers
from apps.user.api.viewsets import UserLoginViewSet
user_router = routers.DefaultRouter()

user_router.register(r'login', UserLoginViewSet)
