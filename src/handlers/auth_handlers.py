"""
Authentication handlers for the Telegram bot.
"""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from config import BOT_PASSWORD, AUTH
from keyboards import get_main_keyboard
from core.user_manager import add_authorized_user, is_user_authorized


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    user_id = update.effective_user.id
    print(f"Received /start command from user {user_id}")

    if BOT_PASSWORD and not is_user_authorized(user_id):
        await update.message.reply_text(
            "🔐 This bot is password protected. Please enter the password to continue:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return AUTH

    context.user_data["web_search"] = False
    context.user_data["url_context"] = False
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        "👋 <b>Welcome to the summarizer bot!</b> Send me a link to get started.",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    print("Welcome message sent successfully")
    return -1  # ConversationHandler.END


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the password entered by the user."""
    password = update.message.text
    user_id = update.effective_user.id

    if password == BOT_PASSWORD:
        add_authorized_user(user_id)
        print(f"User {user_id} authorized successfully.")
        context.user_data["web_search"] = False
        context.user_data["url_context"] = False
        reply_markup = get_main_keyboard()
        await update.message.reply_text(
            "<b>Access granted!</b> ✅ You can now use the bot. Send me a link to get started.",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return -1  # ConversationHandler.END
    else:
        print(f"User {user_id} entered wrong password.")
        await update.message.reply_text(
            "⛔ Wrong password. Please try again.", parse_mode="HTML"
        )
        return AUTH


async def cancel_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the authentication process."""
    await update.message.reply_text(
        "❌ Authentication canceled. Use /start to try again."
    )
    return -1  # ConversationHandler.END
