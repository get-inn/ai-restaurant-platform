from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Celery
celery_app = Celery(
    "restaurant_platform",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
    include=[
        "src.worker.tasks.supplier.document_processing_tasks",
        "src.worker.tasks.supplier.reconciliation_tasks",
        "src.worker.tasks.bots.webhook_tasks",
    ],
)

# Optional configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
)

# Setup Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-telegram-webhooks': {
        'task': 'src.worker.tasks.bots.webhook_tasks.check_telegram_webhooks',
        'schedule': 300.0,  # 5 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()