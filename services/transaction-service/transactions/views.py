"""Transaction API views."""

from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from events import bus
from .models import Transaction
from .serializers import (
    TransactionCreateSerializer,
    TransactionSerializer,
    TransactionEventSerializer,
)


class TransactionInitiateView(generics.CreateAPIView):
    """Create a transaction in PENDING and publish a Kafka event."""

    queryset = Transaction.objects.all()
    serializer_class = TransactionCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = Transaction.objects.create(**serializer.validated_data)
        published = bus.publish_transaction_event(transaction)
        data = TransactionSerializer(transaction).data
        data["event_published"] = published
        return Response(data, status=201)


class TransactionStatusView(APIView):
    """Move a transaction through the state machine (worker/callback endpoint)."""

    def post(self, request, reference):
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)

        to_status = request.data.get("status")
        reason = request.data.get("reason", "")
        try:
            from .models import transition, InvalidTransitionError

            transaction = transition(transaction, to_status, reason=reason, payload=request.data)
        except (ValueError, InvalidTransitionError) as exc:
            return Response({"detail": str(exc)}, status=400)

        bus.publish_status_event(transaction)
        return Response(TransactionSerializer(transaction).data)


class TransactionDetailView(generics.RetrieveAPIView):
    """Fetch a transaction by reference."""

    lookup_field = "reference"
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class TransactionListView(generics.ListAPIView):
    """Transactions for the authenticated user (sender or recipient)."""

    serializer_class = TransactionSerializer

    def get_queryset(self):
        qs = Transaction.objects.all()
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(sender_id=user_id) | qs.filter(recipient_id=user_id)
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class TransactionHistoryView(APIView):
    """Full event audit trail for a transaction."""

    def get(self, request, reference):
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return Response({"detail": "Not found"}, status=404)
        events = transaction.events.all()
        return Response(TransactionEventSerializer(events, many=True).data)