"""Wallet API views."""

from rest_framework import generics, views, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Wallet, LedgerEntry, Currency, post_entry
from .serializers import WalletSerializer, LedgerEntrySerializer, MoneyOpSerializer, CurrencySerializer


class CurrencyListView(generics.ListAPIView):
    """List active currencies."""

    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer


class WalletCreateView(generics.CreateAPIView):
    """Create a wallet for an owner in a currency."""

    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer


class WalletDetailView(generics.RetrieveAPIView):
    queryset = Wallet.objects.select_related("currency")
    serializer_class = WalletSerializer

    def get_object(self):
        return Wallet.objects.select_related("currency").get(
            owner_id=self.kwargs["owner_id"],
            currency__code=self.kwargs["currency"].upper(),
        )


class WalletByOwnerView(generics.ListAPIView):
    """List all wallets for an owner."""

    serializer_class = WalletSerializer

    def get_queryset(self):
        return Wallet.objects.filter(
            owner_id=self.kwargs["owner_id"]
        ).select_related("currency")


class WalletLedgerView(generics.ListAPIView):
    """Paginated ledger entries for a wallet."""

    serializer_class = LedgerEntrySerializer

    def get_queryset(self):
        return LedgerEntry.objects.filter(
            wallet__owner_id=self.kwargs["owner_id"],
            wallet__currency__code=self.kwargs["currency"].upper(),
        )


class MoneyOperationView(views.APIView):
    """Deposit or withdraw against a wallet's ledger."""

    entry_type = LedgerEntry.CREDIT
    serializer_class = MoneyOpSerializer

    def _get_wallet(self, owner_id, currency):
        return Wallet.objects.select_for_update().get(
            owner_id=owner_id, currency__code=currency.upper()
        )

    def post(self, request, owner_id, currency):
        wallet = self._get_wallet(owner_id, currency)
        if wallet.status != "ACTIVE":
            raise ValidationError("Wallet is not active")

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result, reused = post_entry(
                wallet,
                serializer.validated_data["amount"],
                self.entry_type,
                reference=serializer.validated_data.get("reference", ""),
                description=serializer.validated_data.get("description", ""),
                idempotency_key=serializer.validated_data.get("idempotency_key") or None,
            )
        except DjangoValidationError as exc:
            raise ValidationError({"detail": exc.messages})

        http_code = status.HTTP_200_OK if reused else status.HTTP_201_CREATED
        result["reused"] = reused
        return Response(result, status=http_code)


class DepositView(MoneyOperationView):
    entry_type = LedgerEntry.CREDIT


class WithdrawView(MoneyOperationView):
    entry_type = LedgerEntry.DEBIT