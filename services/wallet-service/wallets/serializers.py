"""Wallet API serializers."""

from decimal import Decimal

from rest_framework import serializers
from .models import Wallet, LedgerEntry, Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ["code", "name", "decimals"]


class WalletSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer(read_only=True)
    currency_code = serializers.CharField(write_only=True)

    class Meta:
        model = Wallet
        fields = ["id", "owner_id", "currency", "currency_code", "balance", "status", "created_at"]
        read_only_fields = ["id", "balance", "status", "created_at"]

    def validate_currency_code(self, value):
        if not Currency.objects.filter(code=value.upper(), is_active=True).exists():
            raise serializers.ValidationError("Unsupported or inactive currency")
        return value.upper()

    def create(self, validated_data):
        currency = Currency.objects.get(code=validated_data.pop("currency_code"))
        return Wallet.objects.create(currency=currency, **validated_data)


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ["id", "entry_type", "amount", "balance_after", "reference", "description", "created_at"]
        read_only_fields = fields


class MoneyOpSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=Decimal("0.00000001"))
    reference = serializers.CharField(max_length=128, required=False, allow_blank=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)