"""Tests for transaction state machine."""

import uuid

from django.test import TestCase
from .models import Transaction, TransactionEvent, transition, InvalidTransitionError


def make_tx(**kwargs):
    defaults = {
        "recipient_id": uuid.uuid4(),
        "amount": "25.00",
        "currency": "EUR",
    }
    defaults.update(kwargs)
    return Transaction.objects.create(**defaults)


class TransactionModelTests(TestCase):
    def test_defaults(self):
        tx = make_tx()
        self.assertEqual(tx.status, "PENDING")
        self.assertEqual(tx.txn_type, "TRANSFER")
        self.assertIsNotNone(tx.reference)

    def test_create_event_recorded(self):
        pass  # events are recorded via transition(), tested below

    def test_transition_records_event(self):
        tx = make_tx()
        transition(tx, "PROCESSING", reason="picked up")
        self.assertEqual(tx.status, "PROCESSING")
        events = list(tx.events.all())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].from_status, "PENDING")
        self.assertEqual(events[0].to_status, "PROCESSING")


class StateMachineTests(TestCase):
    def test_pending_to_success_rejected(self):
        tx = make_tx()
        with self.assertRaises(InvalidTransitionError):
            transition(tx, "SUCCESS")

    def test_happy_path(self):
        tx = make_tx()
        transition(tx, "PROCESSING")
        transition(tx, "SUCCESS", reason="settled")
        self.assertEqual(tx.status, "SUCCESS")

    def test_failure_path(self):
        tx = make_tx()
        transition(tx, "PROCESSING")
        transition(tx, "FAILED", reason="insufficient funds")
        self.assertEqual(tx.status, "FAILED")

    def test_terminal_state_locked(self):
        tx = make_tx()
        transition(tx, "PROCESSING")
        transition(tx, "FAILED")
        with self.assertRaises(InvalidTransitionError):
            transition(tx, "PROCESSING")

    def test_cancelled_from_pending(self):
        tx = make_tx()
        transition(tx, "CANCELLED", reason="user cancelled")
        self.assertEqual(tx.status, "CANCELLED")

    def test_history_in_order(self):
        tx = make_tx()
        transition(tx, "PROCESSING")
        transition(tx, "FAILED", reason="declined")
        statuses = list(tx.events.values_list("from_status", "to_status"))
        self.assertEqual(
            statuses,
            [("PENDING", "PROCESSING"), ("PROCESSING", "FAILED")],
        )