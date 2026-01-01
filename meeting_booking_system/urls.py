from django.urls import path
from .views import health, register_user, login_user

urlpatterns = [
    path("health/", health),
    path("auth/register/", register_user),
    path("auth/login/", login_user),
]
