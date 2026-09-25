"""Django admin for users."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Role, Permission, RolePermission, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["code", "description"]
    search_fields = ["code"]


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ["role", "permission"]


@admin.register(User)
class DupayUserAdmin(UserAdmin):
    list_display = ["email", "username", "role", "is_verified", "kyc_status", "is_active"]
    list_filter = ["role", "kyc_status", "is_active", "is_staff"]
    search_fields = ["email", "username"]
    fieldsets = UserAdmin.fieldsets + (
        ("Dupay Profile", {"fields": ("phone", "role", "is_verified", "kyc_status")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Dupay Profile", {"fields": ("role", "phone")}),
    )