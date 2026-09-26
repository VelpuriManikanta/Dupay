"""Wallet models with double-entry ledger accounting."""

from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError


class Currency(models.Model):
    """Supported currency."""

    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=64)
    decimals = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Wallet(models.Model):
    """A user's wallet, balances held per currency."""

    owner_id = models.UUIDField(db_index=True, help_text="User ID from auth-service")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name="wallets")
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0"))
    status = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVE", "Active"),
            ("FROZEN", "Frozen"),
            ("CLOSED", "Closed"),
        ],
        default="ACTIVE",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["owner_id", "currency"], name="unique_wallet_per_currency"),
        ]
        indexes = [models.Index(fields=["owner_id", "status"])]

    def __str__(self):
        return f"{self.owner_id}: {self.currency} {self.balance}"

    def recalculate_balance(self):
        """Recompute balance from ledger entries (source of truth = ledger)."""
        total = LedgerEntry.objects.filter(wallet=self).aggregate(
            total=models.Sum("amount")
        )["total"]
        self.balance = total or Decimal("0")
        self.save(update_fields=["balance", "updated_at"])
        return self.balance


class LedgerEntry(models.Model):
    """Immutable double-entry ledger row. amount is signed (+credit/-debit)."""

    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="entries")
    entry_type = models.CharField(max_length=10, choices=[(DEBIT, "Debit"), (CREDIT, "Credit")])
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    balance_after = models.DecimalField(max_digits=20, decimal_places=8)
    reference = models.CharField(max_length=128, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["wallet", "-id"]),
        ]

    def __str__(self):
        return f"{self.entry_type} {self.amount}"


class IdempotencyKey(models.Model):
    """Guards against duplicate mutation requests (deposit/withdraw)."""

    key = models.CharField(max_length=128, unique=True, db_index=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="idempotency_keys", null=True, blank=True)
    response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.key


def post_entry(wallet, amount, entry_type, reference="", description="", idempotency_key=None):
    """Atomically append a signed ledger entry and update the wallet balance.

    enforces the invariant: balance = sum(all credit entries) - sum(all debit entries)
    """
    if idempotency_key:
        existing = IdempotencyKey.objects.filter(key=idempotency_key).first()
        if existing:
            return existing.response, True

    if amount <= 0:
        raise DjangoValidationError("Amount must be positive")

    signed = Decimal(amount) if entry_type == LedgerEntry.CREDIT else -Decimal(amount)

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

        if entry_type == LedgerEntry.DEBIT and (wallet.balance + signed) < 0:
            raise DjangoValidationError("Insufficient funds")

        balance_after = wallet.balance + signed
        LedgerEntry.objects.create(
            wallet=wallet,
            entry_type=entry_type,
            amount=amount,
            balance_after=balance_after,
            reference=reference,
            description=description,
        )
        wallet.balance = balance_after
        wallet.updated_at = timezone.now()
        wallet.save(update_fields=["balance", "updated_at"])

        result = {
            "wallet_id": wallet.pk,
            "balance": str(wallet.balance),
            "entry_type": entry_type,
            "amount": str(amount),
        }

        if idempotency_key:
            IdempotencyKey.objects.create(key=idempotency_key, wallet=wallet, response=result)

    return result, False