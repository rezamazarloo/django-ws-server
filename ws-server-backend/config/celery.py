import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "clean_up_old_messages": {
        "task": "chat.tasks.clean_up_old_messages",
        "schedule": crontab(minute="*/1"),  # Run every 1 minutes
    },
}
