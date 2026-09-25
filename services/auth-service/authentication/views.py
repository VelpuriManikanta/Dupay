"""Authentication views."""

from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

from users.models import Role
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = TokenObtainPairSerializer.get_token(user)
        return Response({
            "user": UserSerializer(user).data,
            "access": str(tokens.access_token),
            "refresh": str(tokens),
        }, status=201)


class TokenPairView(TokenObtainPairView):
    """Login — returns access + refresh tokens and the user profile."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if user:
            response.data["user"] = UserSerializer(user).data
        return response


class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user