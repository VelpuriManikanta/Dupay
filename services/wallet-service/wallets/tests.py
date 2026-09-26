"""Tests for wallet models and double-entry ledger."""

import uuid
from decimal import Decimal

from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Currency, Wallet, LedgerEntry, post_entry


class LedgerTests(TestCase):
    def setUp(self):
        self.currency = Currency.objects.create(code="EUR", name="Euro")
        self.owner = uuid.uuid4()
        self.wallet = Wallet.objects.create(owner_id=self.owner, currency=self.currency)

    def test_initial_balance_zero(self):
        self.assertEqual(self.wallet.balance, Decimal("0"))

    def test_deposit_credits_balance(self):
        post_entry(self.wallet, Decimal("100.00"), LedgerEntry.CREDIT, reference="dep-1")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("100.00"))
        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_withdraw_debits_balance(self):
        post_entry(self.wallet, Decimal("100.00"), LedgerEntry.CREDIT, reference="dep-1")
        post_entry(self.wallet, Decimal("40.00"), LedgerEntry.DEBIT, reference="wd-1")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("60.00"))

    def test_insufficient_funds_rejected(self):
        with self.assertRaises(DjangoValidationError):
            post_entry(self.wallet, Decimal("10.00"), LedgerEntry.DEBIT, reference="wd-1")
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_balance_after_tracking(self):
        post_entry(self.wallet, Decimal("50.00"), LedgerEntry.CREDIT)
        post_entry(self.wallet, Decimal("20.00"), LedgerEntry.CREDIT)
        last = LedgerEntry.objects.order_by("-id").first()
        self.assertEqual(last.balance_after, Decimal("70.00"))

    def test_recalculate_balance_from_ledger(self):
        post_entry(self.wallet, Decimal("50.00"), LedgerEntry.CREDIT)
        post_entry(self.wallet, Decimal("30.00"), LedgerEntry.CREDIT)
        self.wallet.balance = Decimal("999")
        self.wallet.save(update_fields=["balance"])
        self.wallet.recalculate_balance()
        self.assertEqual(self.wallet.balance, Decimal("80.00"))

    def test_idempotency_reuses_result(self):
        result1, reused1 = post_entry(
            self.wallet, Decimal("25.00"), LedgerEntry.CREDIT, idempotency_key="op-abc"
        )
        result2, reused2 = post_entry(
            self.wallet, Decimal("25.00"), LedgerEntry.CREDIT, idempotency_key="op-abc"
        )
        self.assertFalse(reused1)
        self.assertTrue(reused2)
        self.assertEqual(result1["balance"], result2["balance"])
        # Only one ledger entry despite two calls
        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_amount_must_be_positive(self):
        with self.assertRaises(DjangoValidationError):
            post_entry(self.wallet, Decimal("-5"), LedgerEntry.CREDIT)

    def test_wallet_unique_per_currency(self):
        with self.assertRaises(Exception):
            Wallet.objects.create(owner_id=self.owner, currency=self.currency)