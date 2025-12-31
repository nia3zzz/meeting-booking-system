from django.urls import path
from .views import health, register_user

urlpatterns = [
    path("health/", health),
    path("auth/register/", register_user),
]
