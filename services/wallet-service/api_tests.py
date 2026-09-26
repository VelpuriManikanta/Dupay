"""API tests for wallet endpoints."""

import uuid

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from wallets.models import Currency, Wallet, LedgerEntry

User = get_user_model()


class WalletAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="walletuser", email="wallet@dupay.com", password="Strongpass123!"
        )
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        self.currency = Currency.objects.create(code="EUR", name="Euro")
        self.owner = uuid.uuid4()
        self.wallet = Wallet.objects.create(owner_id=self.owner, currency=self.currency)

    def test_create_wallet(self):
        response = self.client.post("/api/wallets/", {
            "owner_id": str(uuid.uuid4()),
            "currency_code": "EUR",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["balance"], "0.00000000")
        self.assertEqual(response.data["currency"]["code"], "EUR")

    def test_list_wallets_by_owner(self):
        response = self.client.get(f"/api/wallets/owners/{self.owner}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_wallet_detail(self):
        response = self.client.get(f"/api/wallets/owners/{self.owner}/EUR/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["owner_id"], str(self.owner))

    def test_deposit(self):
        response = self.client.post(f"/api/wallets/owners/{self.owner}/EUR/deposit/", {
            "amount": "100.50",
            "reference": "topup-1",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["balance"], "100.50000000")
        self.wallet.refresh_from_db()
        self.assertEqual(str(self.wallet.balance), "100.50000000")

    def test_withdraw_success(self):
        LedgerEntry.objects.create(wallet=self.wallet, entry_type="CREDIT", amount="100", balance_after="100")
        self.wallet.balance = 100
        self.wallet.save()
        response = self.client.post(f"/api/wallets/owners/{self.owner}/EUR/withdraw/", {
            "amount": "30",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["balance"], "70.00000000")

    def test_withdraw_insufficient_funds(self):
        response = self.client.post(f"/api/wallets/owners/{self.owner}/EUR/withdraw/", {
            "amount": "30",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_idempotent_deposit(self):
        payload = {"amount": "50", "idempotency_key": "op-xyz"}
        first = self.client.post(f"/api/wallets/owners/{self.owner}/EUR/deposit/", payload)
        second = self.client.post(f"/api/wallets/owners/{self.owner}/EUR/deposit/", payload)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertTrue(second.data["reused"])
        self.assertEqual(LedgerEntry.objects.count(), 1)

    def test_ledger_listing(self):
        LedgerEntry.objects.create(wallet=self.wallet, entry_type="CREDIT", amount="5", balance_after="5")
        response = self.client.get(f"/api/wallets/owners/{self.owner}/EUR/ledger/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["entry_type"], "CREDIT")