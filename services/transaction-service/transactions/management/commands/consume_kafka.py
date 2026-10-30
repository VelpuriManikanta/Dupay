"""Run the Kafka status consumer (blocking process)."""

from django.core.management.base import BaseCommand
from events.bus import consume_status_updates


class StatusHandler:
    """Applies status updates arriving on the Kafka status topic."""

    def handle(self, message):
        from transactions.models import Transaction, transition

        reference = message.get("reference")
        to_status = message.get("status")
        if not reference or not to_status:
            return
        try:
            transaction = Transaction.objects.get(reference=reference)
        except Transaction.DoesNotExist:
            return
        try:
            transition(transaction, to_status, reason=message.get("reason", ""))
        except Exception as exc:
            print(f"[consume_kafka] skipped {reference}: {exc}")


class Command(BaseCommand):
    help = "Consume transaction status events from Kafka"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Exit after first batch timeout")

    def handle(self, *args, **options):
        self.stdout.write("Consuming Kafka status events…")
        consume_status_updates(StatusHandler)