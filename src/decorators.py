"""
Custom decorators for the Telegram bot.
"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import BOT_PASSWORD
from core.user_manager import is_user_authorized


def authorized(func):
    """Decorator to check if a user is authorized."""

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_id = update.effective_user.id

        # If no password is set, everyone is authorized
        if not BOT_PASSWORD:
            return await func(update, context, *args, **kwargs)

        if not is_user_authorized(user_id):
            await update.message.reply_text(
                "⛔ Non sei autorizzato. Per favore, usa /start per autenticarti.",
                parse_mode="HTML",
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
