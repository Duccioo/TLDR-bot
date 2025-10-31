"""
Authentication handlers for the Telegram bot.
"""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from config import BOT_PASSWORD, AUTH
from decorators import AUTHORIZED_USERS, is_authorized
from keyboards import get_main_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    user_id = update.effective_user.id
    print(f"Received /start command from user {user_id}")

    if not is_authorized(user_id):
        await update.message.reply_text(
            "🔐 Questo bot è protetto da password. Per favore, inserisci la password per continuare:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return AUTH

    context.user_data["web_search"] = False
    context.user_data["url_context"] = False
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        "👋 <b>Benvenuto nel bot riassuntore!</b> Inviami un link per iniziare.",
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
        AUTHORIZED_USERS.append(user_id)
        print(f"User {user_id} authorized successfully.")
        context.user_data["web_search"] = False
        context.user_data["url_context"] = False
        reply_markup = get_main_keyboard()
        await update.message.reply_text(
            "<b>Accesso consentito!</b> ✅ Ora puoi usare il bot. Inviami un link per iniziare.",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return -1  # ConversationHandler.END
    else:
        print(f"User {user_id} entered wrong password.")
        await update.message.reply_text(
            "⛔ Password errata. Riprova.", parse_mode="HTML"
        )
        return AUTH


async def cancel_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the authentication process."""
    await update.message.reply_text(
        "❌ Autenticazione annullata. Usa /start per riprovare."
    )
    return -1  # ConversationHandler.END
