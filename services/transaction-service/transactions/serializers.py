"""Transaction API serializers."""

from rest_framework import serializers
from .models import Transaction, TransactionEvent


class TransactionCreateSerializer(serializers.ModelSerializer):
    external_id = serializers.CharField(max_length=128, required=False, allow_blank=True)

    class Meta:
        model = Transaction
        fields = ["txn_type", "sender_id", "recipient_id", "currency", "amount", "fee", "external_id"]

    def validate(self, attrs):
        if attrs["amount"] <= 0:
            raise serializers.ValidationError({"amount": "Amount must be positive"})
        if attrs["txn_type"] == "TRANSFER" and attrs.get("sender_id") is None:
            raise serializers.ValidationError({"sender_id": "Sender is required for transfers"})
        if attrs["amount"] < attrs.get("fee", 0) * 100:
            # fee must be a small share of amount — keep business rule tolerant
            raise serializers.ValidationError({"fee": "Fee is too large relative to amount"})
        return attrs


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "external_id",
            "txn_type",
            "sender_id",
            "recipient_id",
            "currency",
            "amount",
            "fee",
            "status",
            "status_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TransactionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionEvent
        fields = ["id", "from_status", "to_status", "reason", "payload", "created_at"]