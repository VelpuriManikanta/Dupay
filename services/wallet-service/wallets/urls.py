"""Wallet API routes."""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.WalletCreateView.as_view(), name="wallet-create"),
    path("currencies/", views.CurrencyListView.as_view(), name="currency-list"),
    path("owners/<uuid:owner_id>/", views.WalletByOwnerView.as_view(), name="wallet-by-owner"),
    path("owners/<uuid:owner_id>/<slug:currency>/", views.WalletDetailView.as_view(), name="wallet-detail"),
    path("owners/<uuid:owner_id>/<slug:currency>/ledger/", views.WalletLedgerView.as_view(), name="wallet-ledger"),
    path("owners/<uuid:owner_id>/<slug:currency>/deposit/", views.DepositView.as_view(), name="wallet-deposit"),
    path("owners/<uuid:owner_id>/<slug:currency>/withdraw/", views.WithdrawView.as_view(), name="wallet-withdraw"),
]