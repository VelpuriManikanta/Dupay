"""Tests for users models and RBAC."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Role, Permission, RolePermission

User = get_user_model()


class RoleModelTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="customer", description="Regular customer")
        self.permission = Permission.objects.create(code="transfer.money")
        RolePermission.objects.create(role=self.role, permission=self.permission)

    def test_create_user_with_role(self):
        user = User.objects.create_user(
            email="user@dupay.com", username="user1", password="Testpass123!"
        )
        user.role = self.role
        user.save()
        self.assertEqual(user.role_name, "customer")

    def test_has_permission(self):
        user = User.objects.create_user(
            email="user@dupay.com", username="user1", password="Testpass123!"
        )
        user.role = self.role
        user.save()
        self.assertTrue(user.has_permission("transfer.money"))
        self.assertFalse(user.has_permission("withdraw.money"))

    def test_has_any_role(self):
        user = User.objects.create_user(
            email="user@dupay.com", username="user1", password="Testpass123!"
        )
        user.role = self.role
        user.save()
        self.assertTrue(user.has_any_role("customer", "admin"))
        self.assertFalse(user.has_any_role("admin"))

    def test_user_without_role_has_no_permissions(self):
        user = User.objects.create_user(
            email="user@dupay.com", username="user1", password="Testpass123!"
        )
        self.assertFalse(user.has_permission("transfer.money"))
        self.assertIsNone(user.role_name)

    def test_unique_email(self):
        User.objects.create_user(
            email="user@dupay.com", username="user1", password="Testpass123!"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="user@dupay.com", username="user2", password="Testpass123!"
            )