"""
Utility functions for authorization, text formatting, and animations.
"""
import asyncio
from functools import wraps
from markdown_it import MarkdownIt
from telegram import Update
from telegram.ext import ContextTypes

# In-memory storage for authorized user IDs
AUTHORIZED_USERS = []

def format_summary_text(text: str) -> str:
    """Converts Markdown text to Telegram-compatible HTML."""
    if not text:
        return ""
    md = MarkdownIt("commonmark", {"breaks": True, "html": False}).enable("strikethrough")
    return md.render(text)

def is_authorized(user_id: int, bot_password: str) -> bool:
    """Checks if a user is authorized."""
    return not bot_password or user_id in AUTHORIZED_USERS

def authorized(bot_password: str):
    """Decorator to protect handlers based on authorization."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            if not is_authorized(update.effective_user.id, bot_password):
                await update.message.reply_text("⛔ Non sei autorizzato.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

async def animate_loading_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, stop_event: asyncio.Event):
    """Animates a loading message by editing it periodically."""
    frames = ["⏳", "⌛", "...", "🕰️"]
    i = 0
    while not stop_event.is_set():
        try:
            await context.bot.edit_message_text(f"Elaborazione{frames[i % len(frames)]}", chat_id=chat_id, message_id=message_id)
            i += 1
            await asyncio.sleep(0.7)
        except Exception:
            break
