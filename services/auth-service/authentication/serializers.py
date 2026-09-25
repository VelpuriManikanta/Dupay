"""Authentication serializers."""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Role

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "phone", "first_name", "last_name"]
        extra_kwargs = {
            "phone": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def create(self, validated_data):
        default_role = Role.objects.filter(name="customer").first()
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],
            phone=validated_data.get("phone", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=default_role,
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "phone",
            "first_name",
            "last_name",
            "is_verified",
            "kyc_status",
            "created_at",
        ]
        read_only_fields = fields