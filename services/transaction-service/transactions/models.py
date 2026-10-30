"""Transaction models with event-sourced status flow."""

import uuid

from django.db import models


class Transaction(models.Model):
    """A money movement between two wallets, processed asynchronously."""

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("CANCELLED", "Cancelled"),
    ]

    TYPE_CHOICES = [
        ("TRANSFER", "Wallet to wallet transfer"),
        ("DEPOSIT", "Top-up deposit"),
        ("WITHDRAWAL", "Withdrawal"),
        ("REFUND", "Refund"),
    ]

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    external_id = models.CharField(max_length=128, blank=True, db_index=True)
    txn_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="TRANSFER")

    sender_id = models.UUIDField(null=True, blank=True, db_index=True)
    recipient_id = models.UUIDField(db_index=True)

    currency = models.CharField(max_length=3, default="EUR")
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    status_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["sender_id", "-id"]),
            models.Index(fields=["recipient_id", "-id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.reference} {self.txn_type} {self.amount} {self.currency} [{self.status}]"

    def transitions(self):
        return self.events.order_by("id")


class TransactionEvent(models.Model):
    """Audit trail of every status transition."""

    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="events"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    reason = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.transaction.reference}: {self.from_status or '-'} → {self.to_status}"


VALID_TRANSITIONS = {
    "PENDING": {"PROCESSING", "FAILED", "CANCELLED"},
    "PROCESSING": {"SUCCESS", "FAILED", "CANCELLED"},
    "SUCCESS": {"REFUND"},
    "FAILED": set(),
    "CANCELLED": set(),
}


class InvalidTransitionError(Exception):
    pass


def transition(transaction, to_status, reason="", payload=None):
    """Apply a state-transition, recording an audit event. Caller saves."""
    if to_status not in VALID_TRANSITIONS.get(transaction.status, set()):
        raise InvalidTransitionError(
            f"Illegal transition {transaction.status} → {to_status}"
        )
    transaction.events.create(
        from_status=transaction.status,
        to_status=to_status,
        reason=reason,
        payload=payload or {},
    )
    transaction.status = to_status
    transaction.status_reason = reason
    transaction.save(update_fields=["status", "status_reason", "updated_at"])
    return transaction