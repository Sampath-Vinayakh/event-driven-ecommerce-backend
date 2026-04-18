from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    change_password,
    login,
    logout,
    me,
    register,
)

urlpatterns = [
    path("register/", register, name="auth-register"),
    path("login/", login, name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", logout, name="auth-logout"),
    path("me/", me, name="auth-me"),
    path("change-password/", change_password, name="auth-change-password"),
]