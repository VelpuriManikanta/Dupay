"""Django admin for transactions."""

from django.contrib import admin
from .models import Transaction, TransactionEvent


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference", "txn_type", "amount", "currency",
        "sender_id", "recipient_id", "status", "created_at",
    ]
    list_filter = ["txn_type", "status", "currency", "created_at"]
    search_fields = ["reference", "external_id", "sender_id", "recipient_id"]
    readonly_fields = ["reference"]
    date_hierarchy = "created_at"


@admin.register(TransactionEvent)
class TransactionEventAdmin(admin.ModelAdmin):
    list_display = ["transaction", "from_status", "to_status", "reason", "created_at"]
    list_filter = ["to_status"]
    search_fields = ["transaction__reference"]
    readonly_fields = ["transaction"]