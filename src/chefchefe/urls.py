from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.financial.views import StatsView
from apps.user.urls import user_router
from apps.restaurant.urls import restaurant_router
from apps.products.urls import bill_router
from api.desktop.urls import router_desktop
from api.app.urls import router_app
router = DefaultRouter()
import os
admin.sites.AdminSite.site_header = os.environ.get('ENVIRONMENT_HEADER', 'Local Administração ChefChefe')
admin.sites.AdminSite.site_title = os.environ.get('ENVIRONMENT_NAME', 'Local ChefChefe')
admin.sites.AdminSite.index_title = os.environ.get('ENVIRONMENT_NAME', 'Local ChefChefe')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('rest_framework.urls')),
    path('api/v1/', include(router.urls)),
    path('api/v1/user/', include(user_router.urls)),
    path('api/v1/products/', include(bill_router.urls)),
    path('api/v1/restaurant/', include(restaurant_router.urls)),
    path('api/v1/desktop/', include(router_desktop.urls)),
    path('api/v1/app/', include(router_app.urls)),
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('relatorio/', StatsView.as_view(), name='stats'),
]
