"""
Command handlers for the Telegram bot.
"""

from telegram import Update
from telegram.ext import ContextTypes
from decorators import authorized
from core.quota_manager import get_quota_summary


@authorized
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a help message when the /help command is issued."""
    await update.message.reply_text(
        "ℹ️ Inviami un link a un articolo e io lo riassumerò per te.\n"
        "Usa la tastiera per scegliere un prompt diverso o controllare le quote API.",
        parse_mode="HTML",
    )


@authorized
async def toggle_web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles web search on or off."""
    context.user_data["web_search"] = not context.user_data.get("web_search", False)
    status = "attiva" if context.user_data["web_search"] else "disattiva"
    await update.message.reply_text(
        f"🌐 Ricerca web <b>{status}</b>.", parse_mode="HTML"
    )


@authorized
async def toggle_url_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles URL context on or off."""
    context.user_data["url_context"] = not context.user_data.get("url_context", False)
    status = "attivo" if context.user_data["url_context"] else "disattivo"
    await update.message.reply_text(
        f"🔗 Contesto URL <b>{status}</b>.", parse_mode="HTML"
    )


@authorized
async def api_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a summary of the API quota usage."""
    summary = get_quota_summary()
    await update.message.reply_text(
        f"📊 <b>Quota API Gemini</b> 📊\n\n{summary}", parse_mode="HTML"
    )
