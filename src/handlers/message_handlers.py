"""
Message handlers for the Telegram bot.
"""

import re
import random
import asyncio
from functools import partial
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from markdown_it import MarkdownIt
from decorators import authorized
from core.extractor import estrai_contenuto_da_url
from core.summarizer import summarize_article
from utils import sanitize_html_for_telegram, format_summary_text, clean_hashtags_format
from config import TITLE_EMOJIS, load_available_models

# Initialize Markdown converter
md = MarkdownIt("commonmark", {"breaks": True, "html": True})


async def animate_loading_message(context, chat_id, message_id, stop_event):
    """Animates a loading message with dots and clock emojis without sending notifications."""
    base_text = "Elaborazione in corso"
    dots = ""
    clock_emojis = [
        "🕐",
        "🕑",
        "🕒",
        "🕓",
        "🕔",
        "🕕",
        "🕖",
        "🕗",
        "🕘",
        "🕙",
        "🕚",
        "🕛",
    ]
    emoji_index = 0
    print(f"Starting animation for message {message_id}", flush=True)
    iteration = 0
    while not stop_event.is_set():
        iteration += 1
        dots = "." * ((len(dots) + 1) % 4)
        emoji = clock_emojis[emoji_index]
        emoji_index = (emoji_index + 1) % len(clock_emojis)
        print(f"Animation iteration {iteration} for message {message_id}", flush=True)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{emoji} {base_text}{dots}",
                parse_mode="HTML",
            )
            print(f"Animation frame {iteration} sent successfully", flush=True)
        except Exception as e:
            # If the message is deleted, stop the animation
            if "Message to edit not found" in str(e):
                print(f"Animation stopped: message not found", flush=True)
                break
            print(f"Error animating message: {e}", flush=True)
        await asyncio.sleep(0.5)
    print(
        f"Animation stopped for message {message_id} after {iteration} iterations",
        flush=True,
    )


@authorized
async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarizes the content of a URL."""
    url = None

    # First, try to extract URL from entities (embedded links)
    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "url":
                url = update.message.text[entity.offset : entity.offset + entity.length]
                break
            elif entity.type == "text_link":
                url = entity.url
                break

    # If not found in entities, search in text with regex
    if not url:
        url_pattern = r"https?://[^\s]+"
        match = re.search(url_pattern, update.message.text)
        if match:
            url = match.group(0)

    if not url:
        await update.message.reply_text(
            "🔗 Per favore, invia un URL valido.", parse_mode="HTML"
        )
        return

    processing_message = await update.message.reply_text(
        "⏳ Elaborazione dell'URL in corso...",
        parse_mode="HTML",
        disable_notification=True,
    )
    stop_animation_event = asyncio.Event()
    animation_task = asyncio.create_task(
        animate_loading_message(
            context,
            update.effective_chat.id,
            processing_message.message_id,
            stop_animation_event,
        )
    )
    # Give the animation task time to start
    await asyncio.sleep(0.1)

    try:
        # Extract content in a separate thread to not block the event loop
        loop = asyncio.get_event_loop()
        article_content = await loop.run_in_executor(None, estrai_contenuto_da_url, url)

        if not article_content:
            stop_animation_event.set()
            await animation_task
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
                text="😥 Impossibile estrarre il contenuto dall'URL.",
                parse_mode="HTML",
            )
            return

        context.user_data["article_content"] = article_content
        default_model = (
            load_available_models()[0]
            if load_available_models()
            else "gemini-2.5-flash"
        )
        model_name = context.user_data.get("short_summary_model", default_model)
        use_web_search = context.user_data.get("web_search", False)
        use_url_context = context.user_data.get("url_context", False)

        # Run summarization in a separate thread to not block the event loop
        # We need to use functools.partial to pass keyword arguments
        summarize_func = partial(
            summarize_article,
            article_content,
            "one_paragraph_summary",
            model_name=model_name,
            use_web_search=use_web_search,
            use_url_context=use_url_context,
        )
        one_paragraph_summary_data = await loop.run_in_executor(None, summarize_func)

        if not one_paragraph_summary_data:
            raise ValueError("Impossibile generare il riassunto.")

        one_paragraph_summary = one_paragraph_summary_data.get("summary")
        context.user_data["one_paragraph_summary"] = one_paragraph_summary

        # Pulisce il formato degli hashtag e formatta il testo
        formatted_summary = clean_hashtags_format(
            format_summary_text(one_paragraph_summary)
        )
        random_emoji = random.choice(TITLE_EMOJIS)
        article_title = article_content.title or "Articolo"

        keyboard = [
            [
                InlineKeyboardButton(
                    "📄 Crea pagina Telegraph", callback_data="create_telegraph_page"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Convert Markdown to HTML and sanitize for Telegram
        html_summary = md.render(formatted_summary)
        sanitized_summary = sanitize_html_for_telegram(html_summary)
        message_text = f"<b>{random_emoji} {article_title}</b>\n\n{sanitized_summary}\n\n<i>Riassunto generato con {model_name}</i>"

        print("Stopping animation...", flush=True)
        stop_animation_event.set()
        await animation_task
        print("Animation task completed", flush=True)

        # Delete loading message and send new message with notification
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
        )

        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    except Exception as e:
        stop_animation_event.set()
        await animation_task
        print(f"Error during summarization: {e}", flush=True)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id,
            text=f"🤖 ERRORE: Impossibile completare la richiesta.\nDettagli: {e}",
            parse_mode="HTML",
        )
