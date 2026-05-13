from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "aurvyz_outreach",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks",
        "app.workers.email_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
)

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    "check-follow-ups-every-hour": {
        "task": "app.workers.tasks.check_follow_ups",
        "schedule": 3600.0, # Every hour (production)
    },
}
