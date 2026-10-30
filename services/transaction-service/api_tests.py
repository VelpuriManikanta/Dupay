"""API tests for transaction endpoints."""

import uuid

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from transactions.models import Transaction, TransactionEvent

User = get_user_model()


class TransactionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="txnuser", email="txn@dupay.com", password="Strongpass123!"
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        self.sender = uuid.uuid4()
        self.recipient = uuid.uuid4()

    def test_initiate_transfer(self):
        response = self.client.post("/api/transactions/", {
            "txn_type": "TRANSFER",
            "sender_id": str(self.sender),
            "recipient_id": str(self.recipient),
            "currency": "EUR",
            "amount": "50.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "PENDING")
        self.assertFalse(response.data["event_published"])  # kafka disabled in tests

    def test_initiate_requires_amount_positive(self):
        response = self.client.post("/api/transactions/", {
            "txn_type": "TRANSFER",
            "sender_id": str(self.sender),
            "recipient_id": str(self.recipient),
            "currency": "EUR",
            "amount": "0",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_requires_sender(self):
        response = self.client.post("/api/transactions/", {
            "txn_type": "TRANSFER",
            "recipient_id": str(self.recipient),
            "currency": "EUR",
            "amount": "10.00",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detail_by_reference(self):
        tx = Transaction.objects.create(
            recipient_id=self.recipient, amount="10", currency="EUR"
        )
        response = self.client.get(f"/api/transactions/{tx.reference}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["amount"], "10.00000000")

    def test_status_transition_via_api(self):
        tx = Transaction.objects.create(
            recipient_id=self.recipient, amount="10", currency="EUR"
        )
        response = self.client.post(f"/api/transactions/{tx.reference}/status/", {
            "status": "PROCESSING",
            "reason": "picked up by worker",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "PROCESSING")
        tx.refresh_from_db()
        self.assertEqual(tx.events.count(), 1)

        # illegal jump rejected: PROCESSING cannot go back to PENDING
        bad = self.client.post(f"/api/transactions/{tx.reference}/status/", {
            "status": "PENDING",
        })
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)

    def test_event_history(self):
        tx = Transaction.objects.create(
            recipient_id=self.recipient, amount="10", currency="EUR"
        )
        TransactionEvent.objects.create(
            transaction=tx, to_status="PROCESSING", reason="worker picked up"
        )
        response = self.client.get(f"/api/transactions/{tx.reference}/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["to_status"], "PROCESSING")

    def test_list_filters_by_user_and_status(self):
        other = uuid.uuid4()
        tx1 = Transaction.objects.create(sender_id=self.sender, recipient_id=self.recipient, amount="5", currency="EUR")
        Transaction.objects.create(sender_id=other, recipient_id=other, amount="5", currency="EUR")
        response = self.client.get(
            f"/api/transactions/list/?user_id={self.sender}&status=PENDING"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], tx1.id)