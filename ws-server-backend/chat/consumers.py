# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage
from .tasks import delayed_log_message
import logging

logger = logging.getLogger("chat_logger")


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user from session (can be None for anonymous users)
        self.user = self.scope["user"] if self.scope["user"].is_authenticated else None
        self.room_group_name = "global_chat"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Always accept connection (both authenticated and anonymous)
        await self.accept()

        # Send welcome message
        username = self.user.username if self.user else "Anonymous"
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "username": username,
                "is_authenticated": self.user is not None,
            },
        )

        # Log connection
        logger.info(f"User {username} connected to chat")

    async def disconnect(self, close_code):
        # Send user left message
        username = self.user.username if self.user else "Anonymous"
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "username": username,
                "is_authenticated": self.user is not None,
            },
        )

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Log disconnection
        logger.info(f"User {username} disconnected from chat")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get("type", "chat_message")

            if message_type == "chat_message":
                message = text_data_json.get("message", "").strip()

                if not message:
                    await self.send(text_data=json.dumps({"error": "Message cannot be empty"}))
                    return

                # Save message to database (async)
                saved_message = await self.save_message(message)

                # Get username for display
                username = self.user.username if self.user else "Anonymous"

                # Trigger background task to log message received
                delayed_log_message.delay(f"Message received from {username}.")

                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "username": username,
                        "message_id": saved_message.id,
                        "timestamp": saved_message.created_at.isoformat(),
                        "is_authenticated": self.user is not None,
                    },
                )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON format"}))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({"error": "An error occurred while processing your message"}))

    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        timestamp = event["timestamp"]
        message_id = event["message_id"]
        is_authenticated = event["is_authenticated"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "type": "chat_message",
                    "message": message,
                    "username": username,
                    "message_id": message_id,
                    "timestamp": timestamp,
                    "is_authenticated": is_authenticated,
                }
            )
        )

    async def user_joined(self, event):
        username = event["username"]
        is_authenticated = event["is_authenticated"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "message": f"{username} joined the chat",
                    "username": username,
                    "is_authenticated": is_authenticated,
                }
            )
        )

    async def user_left(self, event):
        username = event["username"]
        is_authenticated = event["is_authenticated"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "message": f"{username} left the chat",
                    "username": username,
                    "is_authenticated": is_authenticated,
                }
            )
        )

    @database_sync_to_async
    def save_message(self, message):
        """Save message to database - user can be None for anonymous users"""
        return ChatMessage.objects.create(message=message, user=self.user)  # Will be None for anonymous users

    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        """Get recent messages from database"""
        return list(ChatMessage.objects.select_related("user").order_by("-created_at")[:limit])
