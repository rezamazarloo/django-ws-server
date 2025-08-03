from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow anonymous users
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {'Anonymous' if not self.user else self.user.username} at {self.created_at}"
