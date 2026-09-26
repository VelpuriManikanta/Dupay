"""Django admin for wallets."""

from django.contrib import admin
from .models import Currency, Wallet, LedgerEntry, IdempotencyKey


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "decimals", "is_active"]
    search_fields = ["code", "name"]


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["pk", "owner_id", "currency", "balance", "status", "created_at"]
    list_filter = ["currency", "status"]
    search_fields = ["owner_id"]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["wallet", "entry_type", "amount", "balance_after", "reference", "created_at"]
    list_filter = ["entry_type", "created_at"]
    search_fields = ["reference"]


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ["key", "wallet", "created_at"]
    search_fields = ["key"]