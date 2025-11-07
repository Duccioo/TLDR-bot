"""
Callback handlers for the Telegram bot.
"""

import random
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from markdown_it import MarkdownIt
from core.summarizer import summarize_article
from core.scraper import crea_articolo_telegraph_with_content
from utils import format_summary_text, sanitize_html_for_telegram, clean_hashtags_format
from config import TITLE_EMOJIS, load_available_models
from handlers.message_handlers import animate_loading_message

# Initialize Markdown converter
md = MarkdownIt("commonmark", {"breaks": True, "html": True})


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

        telegraph_body, telegraph_hashtags = clean_hashtags_format(
            technical_summary or ""
        )
        telegraph_content = telegraph_body
        if telegraph_hashtags:
            telegraph_content = f"{telegraph_hashtags}\n\n{telegraph_body}".strip()

        telegraph_url = await crea_articolo_telegraph_with_content(
            title=article_content.title or "Summary",
            content=telegraph_content,
            author_name=article_content.author or "Summarizer Bot",
            image_urls=image_urls,
            original_url=article_content.url,
        )

        random_emoji = random.choice(TITLE_EMOJIS)
        article_title = article_content.title or "Articolo"

        short_summary_markdown = format_summary_text(one_paragraph_summary)
        short_summary_body, short_summary_hashtags = clean_hashtags_format(
            short_summary_markdown
        )

        html_summary_body = sanitize_html_for_telegram(
            md.render(short_summary_body)
        ).strip()
        html_hashtags = (
            sanitize_html_for_telegram(md.render(short_summary_hashtags)).strip()
            if short_summary_hashtags
            else ""
        )

        message_chunks = [f"<b>{random_emoji} {article_title}</b>"]
        if html_hashtags:
            message_chunks.append(html_hashtags)
        if html_summary_body:
            message_chunks.append(html_summary_body)
        message_chunks.append(
            f'📄 <a href="{telegraph_url}">Leggi il riassunto completo qui</a>'
        )
        message_chunks.append(f"<i>Riassunto generato con {model_name}</i>")

        message_text = "\n\n".join(chunk for chunk in message_chunks if chunk)

        stop_animation_event.set()
        await animation_task

        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=message_text,
            parse_mode="HTML",
        )
        await context.bot.delete_message(
            chat_id=query.message.chat_id, message_id=processing_message.message_id
        )

        # Rimuove i dati dell'articolo per liberare memoria
        if (
            "articles" in context.user_data
            and article_id in context.user_data["articles"]
        ):
            del context.user_data["articles"][article_id]

    except Exception as e:
        stop_animation_event.set()
        await animation_task
        print(f"Error generating Telegraph page: {e}", flush=True)
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=processing_message.message_id,
            text=f"🤖 ERRORE: Impossibile creare la pagina Telegraph.\nDettagli: {e}",
            parse_mode="HTML",
        )
