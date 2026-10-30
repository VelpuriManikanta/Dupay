"""Kafka event publishing and consumption.

Fails safe: if Kafka is unavailable or disabled, events are logged and
skipped so the API keeps working in development.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_producer = None


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer
    try:
        from kafka import KafkaProducer

        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
        )
    except Exception as exc:  # broker down / library missing
        logger.warning("Kafka producer unavailable: %s", exc)
        _producer = None
    return _producer


def publish(topic, key, payload):
    """Publish an event; no-ops (with log) when Kafka is disabled/unreachable."""
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka disabled; event on %s keyspace=%s: %s", topic, key, payload)
        return False
    producer = _get_producer()
    if producer is None:
        logger.warning("Kafka unreachable; dropped event on %s: %s", topic, payload)
        return False
    try:
        producer.send(topic, key=str(key), value=payload).get(timeout=10)
        return True
    except Exception as exc:
        logger.warning("Kafka publish failed (%s): %s", topic, exc)
        return False


def publish_transaction_event(transaction, event_type="transaction.created"):
    """Publish a transaction lifecycle event."""
    payload = {
        "event": event_type,
        "reference": str(transaction.reference),
        "type": transaction.txn_type,
        "sender_id": str(transaction.sender_id) if transaction.sender_id else None,
        "recipient_id": str(transaction.recipient_id),
        "amount": str(transaction.amount),
        "currency": transaction.currency,
        "status": transaction.status,
        "reason": transaction.status_reason,
    }
    return publish(settings.KAFKA_TOPIC_TRANSACTIONS, transaction.reference, payload)


def publish_status_event(transaction, event_type="transaction.status"):
    payload = {
        "event": event_type,
        "reference": str(transaction.reference),
        "status": transaction.status,
        "reason": transaction.status_reason,
    }
    return publish(settings.KAFKA_TOPIC_STATUS, transaction.reference, payload)


def consume_status_updates(HandlerClass=None):
    """Blocking consumer for the status topic. Intended to run as its own process:

        python manage.py consume_kafka

    Applies the handler to each message; each message is committed after a
    successful handler run (at-least-once semantics — handler must be idempotent).
    """
    from kafka import KafkaConsumer

    consumer = KafkaConsumer(
        settings.KAFKA_TOPIC_STATUS,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id="transaction-status-handlers",
    )
    for message in consumer:
        try:
            handler = HandlerClass() if HandlerClass else None
            if handler:
                handler.handle(message.value)
            consumer.commit()
        except Exception as exc:
            logger.warning("Status handler failed: %s (offset %s)", exc, message.offset)