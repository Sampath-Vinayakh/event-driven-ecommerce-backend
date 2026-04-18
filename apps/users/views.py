from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import (
    AuthTokensSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .services import AuthService


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()
    tokens = AuthService.get_tokens_for_user(user)

    response_data = {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": UserSerializer(user).data,
    }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data["user"]
    tokens = AuthService.get_tokens_for_user(user)

    response_data = {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": UserSerializer(user).data,
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    serializer = LogoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    if request.method == "GET":
        return Response(UserSerializer(request.user).data)

    serializer = UserUpdateSerializer(instance=request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)