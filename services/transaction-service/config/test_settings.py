"""Test settings — uses SQLite and disables Kafka so tests run hermetically."""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

KAFKA_ENABLED = False