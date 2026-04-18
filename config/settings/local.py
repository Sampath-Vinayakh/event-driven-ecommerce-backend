from .base import *
import environ
from pathlib import Path

env = environ.Env()

DEBUG = env("DEBUG")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-dev-only-fallback-key-change-me",
)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"],
)


DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://postgres:postgres@localhost:5432/ecommerce",
    )
}


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env(
            "REDIS_URL",
            default="redis://localhost:6379/0",
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": env("REDIS_KEY_PREFIX", default="ecom"),
        "TIMEOUT": env.int("REDIS_CACHE_TIMEOUT", default=300),
    }
}


CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default="redis://localhost:6379/1",
)

CELERY_RESULT_BACKEND = env(
    "CELERY_RESULT_BACKEND",
    default="redis://localhost:6379/2",
)

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

CELERY_TIMEZONE = env("CELERY_TIMEZONE", default="Asia/Kolkata")

CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_TRACK_STARTED = env.bool("CELERY_TASK_TRACK_STARTED", default=True)
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT", default=30 * 60)
CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT", default=25 * 60)


KAFKA_BOOTSTRAP_SERVERS = env(
    "KAFKA_BOOTSTRAP_SERVERS",
    default="localhost:29092",
)

KAFKA_EVENTS_TOPIC = env(
    "KAFKA_EVENTS_TOPIC",
    default="domain-events",
)

KAFKA_CLIENT_ID = env(
    "KAFKA_CLIENT_ID",
    default="ecommerce-backend",
)


EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="noreply@example.com",
)


RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")