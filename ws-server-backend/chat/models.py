from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow anonymous users
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        formatted_time = self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"Message by {'Anonymous' if not self.user else self.user.username} at {formatted_time}"
