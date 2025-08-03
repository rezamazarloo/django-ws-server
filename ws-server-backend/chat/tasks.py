from celery import shared_task
import logging
import time
from datetime import timedelta
from django.utils import timezone
from .models import ChatMessage

logger = logging.getLogger("chat_logger")


@shared_task
def delayed_log_message(message, delay_seconds=5):
    """
    Logs a message to chat.log after a delay.
    """
    time.sleep(delay_seconds)
    logger.info(message)
    return f"Logged message after {delay_seconds} seconds"


@shared_task
def clean_up_old_messages():
    ten_min_ago = timezone.now() - timedelta(minutes=10)
    old_messages = ChatMessage.objects.filter(created_at__lt=ten_min_ago)
    old_messages.delete()  # Deleting messages older 10 minutes ago
    return "Old messages cleaned up"
