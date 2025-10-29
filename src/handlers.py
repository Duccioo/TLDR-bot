"""
Telegram bot handlers for commands, messages, and callbacks.
"""
import re
import html
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from .core.extractor import estrai_contenuto_da_url
from .core.summarizer import summarize_article
from .core.scraper import crea_articolo_telegraph_with_content
from .core.quota_manager import get_quota_summary
from .ui import main_keyboard, TITLE_EMOJIS
from .utils import animate_loading_message, format_summary_text, AUTHORIZED_USERS

# Conversation states
CHOOSE_PROMPT, CHOOSE_MODEL, AUTH = 1, 2, 3

def summarization_worker(url: str, user_data: dict, summary_type: str = "one_paragraph_summary"):
    """Worker function to run blocking summarization tasks."""
    article = estrai_contenuto_da_url(url)
    if not article:
        return None, "Impossibile estrarre contenuto."

    summary = summarize_article(
        article,
        summary_type,
        user_data.get("model", "gemini-2.5-flash"),
        user_data.get("web_search", False),
    )
    if not summary:
        return None, "Impossibile generare riassunto."

    return article, summary

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_password: str):
    """Handles the /start command."""
    from .utils import is_authorized
    if not is_authorized(update.effective_user.id, bot_password):
        await update.message.reply_text("🔐 Inserisci la password:")
        return AUTH
    context.user_data.update({"web_search": False, "url_context": False})
    await update.message.reply_text(
        "👋 <b>Benvenuto!</b> Inviami un link.",
        reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True),
        parse_mode="HTML",
    )
    return ConversationHandler.END

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_password: str):
    """Validates the password."""
    if update.message.text == bot_password:
        AUTHORIZED_USERS.append(update.effective_user.id)
        await update.message.reply_text(
            "<b>Accesso consentito!</b> ✅",
            reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True),
            parse_mode="HTML",
        )
        return ConversationHandler.END
    await update.message.reply_text("⛔ Password errata.")
    return AUTH

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays a help message."""
    await update.message.reply_text("ℹ️ Inviami un link per un riassunto.")

async def toggle_web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles web search."""
    context.user_data["web_search"] = not context.user_data.get("web_search", False)
    status = "attiva" if context.user_data["web_search"] else "disattiva"
    await update.message.reply_text(f"🌐 Ricerca web <b>{status}</b>.", parse_mode="HTML")

async def toggle_url_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles URL context."""
    context.user_data["url_context"] = not context.user_data.get("url_context", False)
    status = "attivo" if context.user_data["url_context"] else "disattivo"
    await update.message.reply_text(f"🔗 Contesto URL <b>{status}</b>.", parse_mode="HTML")

async def choose_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt_keyboard: list):
    """Starts prompt selection."""
    await update.message.reply_text("📝 Scegli un prompt:", reply_markup=ReplyKeyboardMarkup(prompt_keyboard, resize_keyboard=True))
    return CHOOSE_PROMPT

async def prompt_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles prompt selection."""
    context.user_data["prompt"] = update.message.text
    await update.message.reply_text(f"👍 Prompt: <b>{context.user_data['prompt']}</b>", reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True), parse_mode="HTML")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the current operation."""
    await update.message.reply_text("❌ Annullato.", reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True))
    return ConversationHandler.END

async def choose_model_start(update: Update, context: ContextTypes.DEFAULT_TYPE, model_keyboard: list):
    """Starts model selection."""
    await update.message.reply_text("🤖 Scegli un modello:", reply_markup=ReplyKeyboardMarkup(model_keyboard, resize_keyboard=True))
    return CHOOSE_MODEL

async def model_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles model selection."""
    context.user_data["model"] = update.message.text
    await update.message.reply_text(f"👍 Modello: <b>{context.user_data['model']}</b>", reply_markup=ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True), parse_mode="HTML")
    return ConversationHandler.END

async def api_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays API quota."""
    await update.message.reply_text(f"📊 <b>Quota API</b>\n\n{get_quota_summary()}", parse_mode="HTML")

async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles a URL, runs summarization, and sends a summary."""
    url_match = re.search(r"https?://[^\s]+", update.message.text)
    if not url_match:
        return await update.message.reply_text("🔗 URL non valido.")

    msg = await update.message.reply_text("⏳ Elaborazione...")
    stop_event = asyncio.Event()
    anim_task = asyncio.create_task(animate_loading_message(context, msg.chat_id, msg.message_id, stop_event))

    try:
        article, summary_data = await asyncio.to_thread(summarization_worker, url_match.group(0), context.user_data)
        stop_event.set(); await anim_task
        if not article:
            return await msg.edit_text(summary_data)

        context.user_data.update({"article": article, "one_paragraph_summary": summary_data})
        title = html.escape(article.title or "Articolo")
        model = context.user_data.get("model", "gemini-2.5-flash")
        text = f"📰 <b>{title}</b>\n\n{format_summary_text(summary_data['summary'])}\n\n<i>Con {model}</i>"

        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📄 Crea Telegraph", callback_data="create_telegraph_page")]]), parse_mode="HTML")
    except Exception as e:
        stop_event.set(); await anim_task
        await msg.edit_text(f"🤖 ERRORE: {e}")

async def generate_telegraph_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates a detailed summary and posts it to Telegraph."""
    query = update.callback_query
    await query.answer()
    msg = await query.message.reply_text("⏳ Creazione Telegraph con riassunto dettagliato...")

    try:
        _, summary_data = await asyncio.to_thread(
            summarization_worker,
            context.user_data["article"].url,
            context.user_data,
            summary_type=context.user_data.get("prompt", "technical_summary"),
        )
        if not summary_data: raise ValueError("Creazione riassunto dettagliato fallita.")

        article = context.user_data["article"]
        url = crea_articolo_telegraph_with_content(
            article.title or "Summary", summary_data["summary"], article.author or "Bot", summary_data["images"]
        )
        if not url: raise ValueError("Creazione Telegraph fallita.")

        title = html.escape(article.title or "Articolo")
        model = context.user_data.get("model", "gemini-2.5-flash")
        initial_summary_text = format_summary_text(context.user_data["one_paragraph_summary"]["summary"])
        text = f'📰 <b>{title}</b>\n\n{initial_summary_text}\n\n📄 <a href="{url}">Leggi riassunto completo</a>\n\n<i>Con {model}</i>'

        await query.message.edit_text(text, parse_mode="HTML"); await msg.delete()
    except Exception as e:
        await msg.edit_text(f"🤖 ERRORE: {e}")
