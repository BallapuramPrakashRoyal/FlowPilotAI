"""Celery application configuration with transparent Redis resilience."""

import socket
import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)


def is_redis_available(host="localhost", port=6379, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


_redis_up = is_redis_available()
if _redis_up:
    broker_url = settings.REDIS_URL
    backend_url = settings.REDIS_URL
else:
    logger.info("Redis not detected on localhost:6379. Engaging standalone memory transport.")
    broker_url = "memory://"
    backend_url = "cache+memory://"

celery_app = Celery(
    "flowpilot_worker",
    broker=broker_url,
    backend=backend_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    broker_connection_retry_on_startup=False,
    beat_schedule={
        "recover-interrupted-executions": {
            "task": "recover_interrupted_executions",
            "schedule": 300.0,
        },
    },
)

# Register local tasks for both the worker process and API-side dispatch.
import app.workers.tasks as _tasks  # noqa: E402,F401
