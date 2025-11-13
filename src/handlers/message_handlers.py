"""
Message handlers for the Telegram bot.
"""

import re
import random
import asyncio
import hashlib

import telegramify_markdown
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError
from telegram.ext import ContextTypes
from decorators import authorized
from core.extractor import scrape_article
from core.summarizer import summarize_article
from core.history_manager import add_to_history
from utils import format_summary_text, parse_hashtags
from config import TITLE_EMOJIS, load_available_models


async def animate_loading_message(
    context, chat_id, message_id, stop_event, fallback_mode=False
):
    """
    Animates a loading message.
    Uses clock emojis by default or an "angry" sequence in fallback mode.
    """
    base_text = "Processing in progress"
    dots = ""

    if fallback_mode:
        emojis = ["😊", "😐", "😠", "😡"]
        base_text = "Standard extraction failed, using alternative method"
    else:
        emojis = [
            "🕐", "🕑", "🕒", "🕓", "🕔", "🕕",
            "🕖", "🕗", "🕘", "🕙", "🕚", "🕛",
        ]

    emoji_index = 0
    iteration = 0

    while not stop_event.is_set():
        iteration += 1
        dots = "." * ((len(dots) + 1) % 4)
        emoji = emojis[emoji_index]

        if fallback_mode:
            if emoji_index < len(emojis) - 1:
                emoji_index += 1
        else:
            emoji_index = (emoji_index + 1) % len(emojis)

        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{emoji} {base_text}{dots}",
                parse_mode="HTML",
            )
        except Exception as e:
            if "Message to edit not found" in str(e):
                print("Animation stopped: message not found.")
                break
            if "Message is not modified" not in str(e):
                print(f"Error during animation: {e}")

        await asyncio.sleep(0.8 if fallback_mode else 0.5)


@authorized
async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarizes the content of a URL."""
    url = None

    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "text_link":
                url = entity.url
                break

        if not url:
            for entity in update.message.entities:
                if entity.type == "url":
                    url = update.message.text[
                        entity.offset : entity.offset + entity.length
                    ]
                    break

    if not url:
        url_pattern = r"https?://[^\s<>\"'\[\]]+"
        match = re.search(url_pattern, update.message.text)
        if match:
            url = match.group(0).rstrip(".,;!)]")

    if url:
        url = url.strip()
        url = re.sub(r"[\[\]]+$", "", url)

    if not url:
        try:
            await update.message.reply_text(
                "🔗 Please send a valid URL.", parse_mode="HTML"
            )
        except NetworkError as e:
            print(f"Network error sending invalid URL message: {e}")
        return

    try:
        processing_message = await update.message.reply_text(
            "⏳ Processing URL...",
            parse_mode="HTML",
            disable_notification=True,
        )
    except NetworkError as e:
        print(f"Network error sending processing message: {e}")
        return

    stop_animation_event = asyncio.Event()
    animation_task = None

    try:
        article_content, fallback_used, error_details = await scrape_article(url)

        animation_task = asyncio.create_task(
            animate_loading_message(
                context,
                update.effective_chat.id,
                processing_message.message_id,
                stop_animation_event,
                fallback_mode=fallback_used,
            )
        )

        if not article_content:
            if animation_task:
                stop_animation_event.set()
                await animation_task

            error_message = (
                f"😥 <b>Unable to extract content from the URL.</b>\n"
                f"Here are the technical details:\n<pre>{error_details}</pre>"
            )

            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=processing_message.message_id,
                    text=error_message,
                    parse_mode="HTML",
                )
            except NetworkError as e:
                print(
                    f"Network error trying to update scraping error message: {e}"
                )
            return

        article_id = hashlib.sha256(url.encode()).hexdigest()[:32]
        if "articles" not in context.user_data:
            context.user_data["articles"] = {}

        context.user_data["articles"][article_id] = {"article_content": article_content}

        default_model = (
            load_available_models()[0]
            if load_available_models()
            else "gemini-2.5-flash"
        )
        random_emoji = random.choice(TITLE_EMOJIS)
        model_name = context.user_data.get("short_summary_model", default_model)
        use_web_search = context.user_data.get("web_search", False)
        use_url_context = context.user_data.get("url_context", False)

        one_paragraph_summary_data = await summarize_article(
            article_content,
            "one_paragraph_summary_V2",
            model_name=model_name,
            use_web_search=use_web_search,
            use_url_context=use_url_context,
        )

        if not one_paragraph_summary_data:
            raise ValueError("Could not generate summary.")

        one_paragraph_summary = one_paragraph_summary_data.get("summary")

        llm_hashtags = []
        summary_text_clean = one_paragraph_summary

        hashtag_match = re.match(r"^(#\S+(?:\s+#\S+)*)\s*", one_paragraph_summary)
        if hashtag_match:
            hashtag_line = hashtag_match.group(1)
            llm_hashtags = parse_hashtags(hashtag_line)
            summary_text_clean = one_paragraph_summary[hashtag_match.end() :].strip()

        summary_text_clean = re.sub(
            r"^(?:[^\n]*?)\s*(#\S+(?:\s+#\S+)*)\s*$",
            lambda m: (
                m.group(0).replace(m.group(1), "").strip() if m.group(1) else m.group(0)
            ),
            summary_text_clean,
            flags=re.MULTILINE,
        )

        embedded_hashtag_match = re.search(
            r"📌\s*(#\S+(?:\s+#\S+)*)", summary_text_clean
        )
        if embedded_hashtag_match:
            embedded_hashtags = parse_hashtags(embedded_hashtag_match.group(1))
            llm_hashtags.extend(embedded_hashtags)
            summary_text_clean = re.sub(
                r"\n?.*?📌\s*#\S+(?:\s+#\S+)*.*?\n?", "\n", summary_text_clean
            ).strip()

        final_hashtags = []
        if article_content.tags:
            final_hashtags = [
                f"#{tag.strip().replace(' ', '_')}" for tag in article_content.tags
            ]
        else:
            final_hashtags = llm_hashtags

        context.user_data["articles"][article_id][
            "one_paragraph_summary"
        ] = summary_text_clean
        context.user_data["articles"][article_id]["hashtags"] = final_hashtags

        user_id = update.effective_user.id
        add_to_history(user_id, url, summary_text_clean, final_hashtags)

        no_hashtags_found = not final_hashtags
        formatted_summary = format_summary_text(summary_text_clean)
        article_title = article_content.title or "Article"

        message_sections = [f"**{random_emoji} {article_title}**"]

        if no_hashtags_found:
            message_sections.append(">No Hashtag")
        else:
            hashtags_line = " ".join(final_hashtags)
            message_sections.append(">" + hashtags_line)

        if formatted_summary:
            message_sections.append(formatted_summary)

        message_sections.append(f"\n_Summary generated with {model_name}_")

        message_markdown = "\n\n".join(
            section for section in message_sections if section
        )

        telegram_message = telegramify_markdown.markdownify(
            message_markdown,
            normalize_whitespace=False,
        )

        keyboard_buttons = [
            InlineKeyboardButton(
                "📄 Create Telegraph Page",
                callback_data=f"create_telegraph_page:{article_id}",
            )
        ]
        if no_hashtags_found:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    "🔄 Retry Hashtags", callback_data=f"retry_hashtags:{article_id}"
                )
            )

        keyboard = [keyboard_buttons]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if animation_task:
            stop_animation_event.set()
            await animation_task

        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=telegram_message,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
                reply_to_message_id=update.message.message_id,
            )
        except NetworkError as e:
            print(f"Network error sending final summary: {e}")

    except NetworkError as e:
        print(f"Unhandled network error during summary process: {e}")
        if animation_task and not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task

    except Exception as e:
        if animation_task and not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task

        print(f"Unexpected error during summary: {e}")
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
                text=f"🤖 ERROR: Could not complete the request.\nDetails: {e}",
                parse_mode="HTML",
            )
        except NetworkError as ne:
            print(
                f"Network error trying to send final error message: {ne}"
            )
