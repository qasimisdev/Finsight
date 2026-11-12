"""Celery worker: long analyses with progress tracking, retries and saved results."""
import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("finsight", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=24 * 3600,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def run_analysis(self, messages: list) -> dict:
    from app.harness import run_chat

    def progress(note: str) -> None:
        self.update_state(state="PROGRESS", meta={"note": note})

    self.update_state(state="PROGRESS", meta={"note": "started"})
    result = run_chat(messages, on_step=progress)
    return result
