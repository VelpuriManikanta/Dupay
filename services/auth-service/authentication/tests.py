"""API tests for authentication endpoints."""

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from users.models import Role

User = get_user_model()


class AuthAPITests(APITestCase):
    def setUp(self):
        Role.objects.create(name="customer", description="Customer")

    def test_register(self):
        response = self.client.post("/auth/register/", {
            "email": "new@dupay.com",
            "username": "newbie",
            "password": "Strongpass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "new@dupay.com")
        self.assertEqual(response.data["user"]["role"], "customer")

    def test_register_duplicate_email(self):
        self.client.post("/auth/register/", {
            "email": "new@dupay.com",
            "username": "newbie",
            "password": "Strongpass123!",
        })
        response = self.client.post("/auth/register/", {
            "email": "new@dupay.com",
            "username": "other",
            "password": "Strongpass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_me(self):
        user = User.objects.create_user(
            email="login@dupay.com", username="loginuser", password="Strongpass123!"
        )
        response = self.client.post("/auth/login/", {
            "email": "login@dupay.com",
            "password": "Strongpass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        me = self.client.get("/auth/me/")
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["email"], "login@dupay.com")

    def test_me_requires_auth(self):
        response = self.client.get("/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_invalid_credentials(self):
        response = self.client.post("/auth/login/", {
            "email": "nobody@dupay.com",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        user = User.objects.create_user(
            email="refresh@dupay.com", username="refreshuser", password="Strongpass123!"
        )
        token = RefreshToken.for_user(user)
        response = self.client.post("/auth/refresh/", {"refresh": str(token)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)