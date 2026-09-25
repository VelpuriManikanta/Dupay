"""Custom User model with roles for RBAC."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    """Application role for RBAC."""

    ROLE_CHOICES = [
        ("customer", "Customer"),
        ("admin", "Administrator"),
        ("compliance", "Compliance Officer"),
        ("support", "Support"),
    ]

    name = models.CharField(max_length=32, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Named application permission."""

    code = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    """Many-to-many link between roles and permissions."""

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name="roles")

    class Meta:
        unique_together = ("role", "permission")

    def __str__(self):
        return f"{self.role.name}:{self.permission.code}"


class User(AbstractUser):
    """Platform user. Extends Django's AbstractUser with role and profile data."""

    ROLES = [choice[0] for choice in Role.ROLE_CHOICES]

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="users", null=True, blank=True
    )
    is_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ("NOT_SUBMITTED", "Not submitted"),
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
        default="NOT_SUBMITTED",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["kyc_status"]),
        ]

    def __str__(self):
        return self.email

    @property
    def role_name(self):
        return self.role.name if self.role else None

    def has_permission(self, code):
        if self.role is None:
            return False
        return self.role.permissions.filter(permission__code=code).exists()

    def has_any_role(self, *role_names):
        return self.role is not None and self.role.name in role_names