"""
Callback handlers for the Telegram bot.
"""

import re
import random
import asyncio
import telegramify_markdown
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.summarizer import summarize_article
from core.scraper import crea_articolo_telegraph_with_content
from core.history_manager import load_history, save_history
from utils import format_summary_text
from config import TITLE_EMOJIS, load_available_models
from handlers.message_handlers import animate_loading_message


async def generate_telegraph_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Creates a Telegraph page with the full summary."""
    query = update.callback_query
    await query.answer()

    try:
        article_id = query.data.split(":")[1]
    except (IndexError, AttributeError):
        await query.message.reply_text("🤖 ERRORE: ID articolo non valido.")
        return

    processing_message = await query.message.reply_text(
        "⏳ Generazione della pagina Telegraph in corso...", parse_mode="HTML"
    )
    stop_animation_event = asyncio.Event()
    animation_task = asyncio.create_task(
        animate_loading_message(
            context,
            query.message.chat_id,
            processing_message.message_id,
            stop_animation_event,
        )
    )

    try:
        article_data = context.user_data.get("articles", {}).get(article_id)
        if not article_data:
            raise ValueError("Impossibile trovare i dati dell'articolo.")

        article_content = article_data.get("article_content")
        one_paragraph_summary = article_data.get("one_paragraph_summary")
        hashtags = article_data.get("hashtags", [])

        if not article_content or not one_paragraph_summary:
            raise ValueError("Dati del riassunto incompleti.")

        default_model = (
            load_available_models()[0]
            if load_available_models()
            else "gemini-1.5-flash"
        )
        model_name = context.user_data.get("telegraph_summary_model", default_model)
        use_web_search = context.user_data.get("web_search", False)
        use_url_context = context.user_data.get("url_context", False)
        technical_summary_prompt = context.user_data.get("prompt", "technical_summary")

        technical_summary_data = await summarize_article(
            article_content,
            summary_type=technical_summary_prompt,
            model_name=model_name,
            use_web_search=use_web_search,
            use_url_context=use_url_context,
        )

        if not technical_summary_data:
            raise ValueError("Impossibile generare il riassunto completo.")

        technical_summary = technical_summary_data.get("summary")
        image_urls = technical_summary_data.get("images")

        # Ensure hashtags from the summary are included in the Telegraph page
        telegraph_content = technical_summary
        if hashtags:
            hashtags_line = " ".join(hashtags)
            telegraph_content = f"{hashtags_line}\n\n{technical_summary}".strip()


        telegraph_url = await crea_articolo_telegraph_with_content(
            title=article_content.title or "Summary",
            content=telegraph_content,
            author_name=article_content.author or "Summarizer Bot",
            image_urls=image_urls,
            original_url=article_content.url,
        )

        # Reconstruct the original message and append the Telegraph link
        original_message_text = query.message.text_markdown_v2
        updated_text = f"{original_message_text}\n\n📄 [Leggi il riassunto completo qui]({telegraph_url})"

        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=updated_text,
            parse_mode="MarkdownV2",
            disable_web_page_preview=True,
            reply_markup=None # Remove keyboard after creating the page
        )

    except Exception as e:
        print(f"Error generating Telegraph page: {e}", flush=True)
        stop_animation_event.set()
        await animation_task
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=processing_message.message_id,
            text=f"🤖 ERRORE: Impossibile creare la pagina Telegraph.\nDettagli: {e}",
            parse_mode="HTML",
        )
    finally:
        if not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task
        await context.bot.delete_message(
            chat_id=query.message.chat_id, message_id=processing_message.message_id
        )
        if 'articles' in context.user_data and article_id in context.user_data['articles']:
            del context.user_data['articles'][article_id]


async def retry_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retries generating hashtags for an article."""
    query = update.callback_query
    await query.answer()

    try:
        article_id = query.data.split(":")[1]
    except (IndexError, AttributeError):
        await query.message.reply_text("🤖 ERRORE: ID articolo non valido.")
        return

    article_data = context.user_data.get("articles", {}).get(article_id)
    if not article_data or "article_content" not in article_data:
        await query.edit_message_text("🤖 ERRORE: Dati dell'articolo scaduti o non trovati. Riprova a inviare l'URL.")
        return

    article_content = article_data["article_content"]

    # Use the same model as the short summary for consistency
    default_model = (
        load_available_models()[0]
        if load_available_models()
        else "gemini-1.5-flash"
    )
    model_name = context.user_data.get("short_summary_model", default_model)

    # Call LLM to get only hashtags
    hashtag_data = await summarize_article(
        article_content,
        "retry_hashtags_prompt",
        model_name=model_name,
    )

    new_hashtags_str = hashtag_data.get("summary") if hashtag_data else ""

    if new_hashtags_str and new_hashtags_str.startswith("#"):
        new_hashtags = [tag.strip() for tag in new_hashtags_str.split()]

        # Update history
        user_id = update.effective_user.id
        history = load_history(user_id)
        for entry in history:
            if entry.get("url") == article_content.url:
                entry["hashtags"] = new_hashtags
                break
        save_history(user_id, history)

        # Reconstruct the original message with the new hashtags
        original_message_text = query.message.text_markdown_v2
        # Replace ">No Hashtag" with the new hashtags
        updated_text = re.sub(r">No Hashtag", ">" + " ".join(new_hashtags), original_message_text)

        # Update keyboard to remove the retry button
        keyboard = [[
            InlineKeyboardButton(
                "📄 Crea pagina Telegraph",
                callback_data=f"create_telegraph_page:{article_id}",
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=updated_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
    else:
        # If it fails again, just show the same message with the button
        await context.bot.answer_callback_query(
            query.id,
            text="😔 Tentativo fallito. Nessun hashtag generato.",
            show_alert=True
        )
