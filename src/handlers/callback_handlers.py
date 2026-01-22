"""
Callback handlers for the Telegram bot.
"""

import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.summarizer import summarize_article
from core.scraper import crea_articolo_telegraph_with_content
from core.history_manager import load_history, save_history
from keyboards import get_retry_keyboard
from utils import parse_hashtags
from config import load_available_models
from handlers.message_handlers import animate_loading_message


async def generate_telegraph_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Creates a Telegraph page with the full summary."""
    query = update.callback_query
    await query.answer()

    try:
        article_id = query.data.split(":")[1]
    except (IndexError, AttributeError):
        await query.message.reply_text("🤖 ERROR: Invalid article ID.")
        return

    processing_message = await query.message.reply_text(
        "⏳ Generating Telegraph page...", parse_mode="HTML"
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
            raise ValueError("Could not find article data.")

        article_content = article_data.get("article_content")
        one_paragraph_summary = article_data.get("one_paragraph_summary")
        hashtags = article_data.get("hashtags", [])

        if not article_content or not one_paragraph_summary:
            raise ValueError("Incomplete summary data.")

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
            raise ValueError("Could not generate the full summary.")

        # Check for retry flag first
        if technical_summary_data.get("needs_retry"):
            error_message = technical_summary_data.get("summary")
            retry_keyboard = get_retry_keyboard(
                article_content.url,
                technical_summary_prompt,
                use_web_search,
                use_url_context,
            )
            await context.bot.edit_message_text(
                chat_id=query.message.chat_id,
                message_id=processing_message.message_id,
                text=error_message,
                parse_mode="HTML",
                reply_markup=retry_keyboard,
            )
            # Stop the animation, but don't delete the message
            stop_animation_event.set()
            await animation_task
            return

        technical_summary = technical_summary_data.get("summary")
        if "ERRORE:" in technical_summary or "ERROR:" in technical_summary:
            raise ValueError(technical_summary)

        image_urls = technical_summary_data.get("images")

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

        original_message_text = query.message.text_html

        # New Telegraph link
        telegraph_link = f'📄 <a href="{telegraph_url}">Read on Telegra.ph</a>\n'

        # Find the "Original Article" link and insert the Telegraph link before it
        # The regex looks for the specific "📖 Original Article" link
        pattern = re.compile(r'(<a href="[^"]+">📖\s*Original Article</a>)', re.IGNORECASE)

        # Replace the found pattern with the new link followed by the original link
        updated_text, num_replacements = pattern.subn(
            f"{telegraph_link}\\1", original_message_text
        )

        # If the pattern wasn't found, fall back to appending before the footer
        if num_replacements == 0:
            footer_pattern = re.compile(r'(<i>\s*Summary generated with[^<]*</i>)', re.IGNORECASE)
            match = footer_pattern.search(original_message_text)
            if match:
                footer_html = match.group(1)
                main_content = original_message_text.split(footer_html)[0].strip()
                updated_text = f"{main_content}\n\n{telegraph_link}\n{footer_html}"
            else:
                # Absolute fallback: just append the link
                updated_text = f"{original_message_text.strip()}\n\n{telegraph_link}"

        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            text=updated_text,
            parse_mode="HTML",
            disable_web_page_preview=False,
            reply_markup=None,
        )

    except Exception as e:
        print(f"Error generating Telegraph page: {e}", flush=True)
        stop_animation_event.set()
        await animation_task
        await context.bot.edit_message_text(
            chat_id=query.message.chat_id,
            message_id=processing_message.message_id,
            text=f"🤖 ERROR: Could not create Telegraph page.\nDetails: {e}",
            parse_mode="HTML",
        )
    finally:
        if not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task
        await context.bot.delete_message(
            chat_id=query.message.chat_id, message_id=processing_message.message_id
        )
        if (
            "articles" in context.user_data
            and article_id in context.user_data["articles"]
        ):
            del context.user_data["articles"][article_id]


from handlers.message_handlers import process_url


async def retry_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retries the summarization process for a given URL."""
    query = update.callback_query
    await query.answer()

    try:
        _, summary_type, url, use_web_search_str, use_url_context_str = query.data.split(":", 4)
        use_web_search = use_web_search_str.lower() == 'true'
        use_url_context = use_url_context_str.lower() == 'true'

        # HACK: To keep the flow consistent, we're reusing the process_url function.
        # We need to simulate a "message" object that process_url can use.
        class MockMessage:
            def __init__(self, text, chat_id):
                self.text = text
                self.chat_id = chat_id
                self.message_id = query.message.message_id

            async def reply_text(self, *args, **kwargs):
                # Edit the existing message instead of sending a new one
                return await context.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    *args,
                    **kwargs
                )

        mock_message = MockMessage(url, query.message.chat_id)

        # We also need to remove the "Retry" button from the message we're about to edit.
        await query.edit_message_reply_markup(reply_markup=None)

        # Now, call the main processing function as if a new message with the URL was sent
        await process_url(
            update.effective_chat.id,
            url,
            context,
            mock_message,
            use_web_search,
            use_url_context,
            summary_type, # Pass the original summary type to be retried
        )

    except (ValueError, IndexError) as e:
        print(f"Error in retry_summary callback: {e}", flush=True)
        await query.message.reply_text("🤖 ERROR: Invalid retry data. Please try sending the URL again.")


async def retry_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retries generating hashtags for an article."""
    query = update.callback_query
    await query.answer()

    processing_message = await query.message.reply_text(
        "⏳ Generating hashtags...", parse_mode="HTML"
    )

    try:
        article_id = query.data.split(":")[1]
    except (IndexError, AttributeError):
        await processing_message.edit_text("🤖 ERROR: Invalid article ID.")
        return

    article_data = context.user_data.get("articles", {}).get(article_id)
    if not article_data or "article_content" not in article_data:
        await processing_message.edit_text(
            "🤖 ERROR: Article data expired or not found. Please try sending the URL again."
        )
        return

    article_content = article_data["article_content"]
    use_web_search = context.user_data.get("web_search", False)
    use_url_context = context.user_data.get("url_context", False)

    default_model = (
        load_available_models()[0] if load_available_models() else "gemini-1.5-flash"
    )
    model_name = context.user_data.get("short_summary_model", default_model)

    hashtag_data = await summarize_article(
        article_content,
        "retry_hashtags_prompt",
        model_name=model_name,
        use_web_search=use_web_search,
        use_url_context=use_url_context,
    )

    if not hashtag_data:
        await processing_message.edit_text("🤖 ERROR: Could not generate hashtags.")
        return

    if hashtag_data.get("needs_retry"):
        error_message = hashtag_data.get("summary")
        retry_keyboard = get_retry_keyboard(
            article_content.url,
            "retry_hashtags_prompt",
            use_web_search,
            use_url_context,
        )
        await processing_message.edit_text(
            error_message, parse_mode="HTML", reply_markup=retry_keyboard
        )
        return

    # On success, delete the processing message
    await processing_message.delete()

    new_hashtags_str = hashtag_data.get("summary")
    if new_hashtags_str and new_hashtags_str.startswith("#"):
        new_hashtags = parse_hashtags(new_hashtags_str)
        user_id = update.effective_user.id
        history = load_history(user_id)
        for entry in history:
            if entry.get("url") == article_content.url:
                entry["hashtags"] = new_hashtags
                break
        save_history(user_id, history)

        original_message_text = query.message.text_markdown_v2
        escaped_hashtags = " ".join([tag.replace("#", r"\\#") for tag in new_hashtags])
        updated_text = re.sub(
            r">No Hashtag", ">" + escaped_hashtags, original_message_text
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📄 Create Telegraph Page",
                    callback_data=f"create_telegraph_page:{article_id}",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=updated_text, reply_markup=reply_markup, parse_mode="MarkdownV2"
        )
    else:
        await context.bot.answer_callback_query(
            query.id,
            text="😔 Attempt failed. No hashtags generated.",
            show_alert=True,
        )
