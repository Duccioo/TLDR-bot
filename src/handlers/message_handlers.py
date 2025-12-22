"""
Message handlers for the Telegram bot.
"""

import re
import random
import asyncio
import hashlib

import telegramify_markdown
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import NetworkError, TelegramError
from telegram.ext import ContextTypes
from decorators import authorized
from core.extractor import scrape_article, ArticleContent
from core.summarizer import summarize_article, answer_question
from core.history_manager import add_to_history
from keyboards import get_retry_keyboard
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

        await asyncio.sleep(1.5)


async def process_url(
    chat_id: int,
    url: str,
    context: ContextTypes.DEFAULT_TYPE,
    message: Update.message,
    use_web_search: bool,
    use_url_context: bool,
    summary_type: str,
):
    """
    Processes a URL by scraping, summarizing, and sending the result.
    This function is designed to be reusable for both new messages and retries.
    """
    processing_message = await message.reply_text(
        "⏳ Processing URL...",
        parse_mode="HTML",
        disable_notification=True,
    )

    stop_animation_event = asyncio.Event()
    animation_task = None

    try:
        async with asyncio.timeout(300):  # 5 minutes timeout
            article_content, fallback_used, error_details = await scrape_article(url)

            animation_task = asyncio.create_task(
                animate_loading_message(
                    context,
                    chat_id,
                    processing_message.message_id,
                    stop_animation_event,
                    fallback_mode=fallback_used,
                )
            )

            # Determine model early to check for fallback eligibility
            default_model = (
                load_available_models()[0]
                if load_available_models()
                else "gemini-2.5-flash"
            )
            model_name = context.user_data.get("short_summary_model", default_model)

            if not article_content:
                # Fallback: If Gemini, try to use URL context directly
                if "gemini" in model_name.lower():
                    print(f"Scraping failed for {url}. Attempting Gemini URL context fallback.")
                    article_content = ArticleContent(
                        title="URL Content (Fallback)",
                        text="Content not extracted. Please utilize the available tools (Google Search/URL Context) to read and summarize the content directly from the provided URL.",
                        url=url,
                        tags=[],
                        images=[]
                    )
                    use_web_search = True
                    use_url_context = True
                    fallback_used = True
                else:
                    if animation_task:
                        stop_animation_event.set()
                        await animation_task
                    error_message = (
                        f"😥 <b>Unable to extract content from the URL.</b>\n"
                        f"Here are the technical details:\n<pre>{error_details}</pre>"
                    )
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=processing_message.message_id,
                        text=error_message,
                        parse_mode="HTML",
                    )
                    return

            article_id = hashlib.sha256(url.encode()).hexdigest()[:32]
            if "articles" not in context.user_data:
                context.user_data["articles"] = {}
            context.user_data["articles"][article_id] = {
                "article_content": article_content
            }

            summary_data = await summarize_article(
                article_content,
                summary_type,
                model_name=model_name,
                use_web_search=use_web_search,
                use_url_context=use_url_context,
            )

            if not summary_data:
                raise ValueError("Could not generate summary.")

            # Check for retry flag first
            if summary_data.get("needs_retry"):
                error_message = summary_data.get("summary")
                retry_keyboard = get_retry_keyboard(
                    url, summary_type, use_web_search, use_url_context
                )
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_message.message_id,
                    text=error_message,
                    parse_mode="HTML",
                    reply_markup=retry_keyboard,
                )
                return

            summary_text = summary_data.get("summary")
            if "ERRORE:" in summary_text:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_message.message_id,
                    text=summary_text,
                    parse_mode="HTML",
                )
                return

            # --- Success Case ---
            llm_hashtags = []
            summary_text_clean = summary_text
            hashtag_match = re.match(r"^(#\S+(?:\s+#\S+)*)\s*", summary_text)
            if hashtag_match:
                hashtag_line = hashtag_match.group(1)
                llm_hashtags = parse_hashtags(hashtag_line)
                summary_text_clean = summary_text[hashtag_match.end() :].strip()

            final_hashtags = (
                parse_hashtags(",".join(article_content.tags))
                if article_content.tags
                else llm_hashtags
            )

            context.user_data["articles"][article_id][
                "one_paragraph_summary"
            ] = summary_text_clean
            context.user_data["articles"][article_id]["hashtags"] = final_hashtags

            add_to_history(chat_id, url, summary_text_clean, final_hashtags)

            no_hashtags_found = not final_hashtags
            formatted_summary = format_summary_text(summary_text_clean)
            article_title = article_content.title or "Article"
            random_emoji = random.choice(TITLE_EMOJIS)

            message_sections = [f"**{random_emoji} {article_title}**"]
            if no_hashtags_found:
                message_sections.append(">No Hashtag")
            else:
                message_sections.append(">" + " ".join(final_hashtags))
            message_sections.append(formatted_summary)
            message_sections.append(f"[📖 Original Article]({url})")
            message_sections.append(f"_Summary generated with {model_name}_")

            message_markdown = "\n\n".join(filter(None, message_sections))
            telegram_message = telegramify_markdown.markdownify(
                message_markdown, normalize_whitespace=False
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
            reply_markup = InlineKeyboardMarkup([keyboard_buttons])

            if animation_task:
                stop_animation_event.set()
                await animation_task

            await context.bot.delete_message(
                chat_id=chat_id, message_id=processing_message.message_id
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=telegram_message,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
                reply_to_message_id=message.message_id,
            )

    except TimeoutError:
        if animation_task and not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task
        print(f"URL processing timed out for: {url}", flush=True)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_message.message_id,
                text="⚠️ Request timed out. The operation took longer than 5 minutes. Please try again later.",
                parse_mode="HTML",
            )
        except TelegramError as te:
            print(
                f"Failed to send timeout message due to Telegram API error: {te}",
                flush=True,
            )

    except Exception as e:
        if animation_task and not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task
        print(f"Unexpected error during URL processing: {e}", flush=True)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_message.message_id,
                text=f"🤖 ERROR: Could not complete the request.\nDetails: {e}",
                parse_mode="HTML",
            )
        except TelegramError as te:
            print(
                f"Failed to send error message due to Telegram API error: {te}",
                flush=True,
            )


# Create a queue for processing URLs sequentially
url_queue = asyncio.Queue()


async def url_processor_worker():
    """
    Worker that processes URLs from the queue one by one.
    """
    print("URL processor worker started.", flush=True)
    while True:
        try:
            # Get a URL processing task from the queue
            task_data = await url_queue.get()
            (
                chat_id,
                url,
                context,
                message,
                use_web_search,
                use_url_context,
                summary_type,
            ) = task_data

            print(f"Processing URL from queue: {url}", flush=True)
            await process_url(
                chat_id=chat_id,
                url=url,
                context=context,
                message=message,
                use_web_search=use_web_search,
                use_url_context=use_url_context,
                summary_type=summary_type,
            )
        except Exception as e:
            print(f"Error in URL processor worker: {e}", flush=True)
        finally:
            # Notify the queue that the task is done
            url_queue.task_done()


@authorized
async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles incoming messages with URLs and adds them to the processing queue.
    """
    url_pattern = r"https?://[^\s<>\"'\[\]]+"
    text = ""
    url = None

    message = update.message or update.edited_message
    if not message or not message.text:
        return

    text = message.text
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link" and hasattr(entity, "url") and entity.url:
                url = entity.url
                break
        if not url:
            for entity in message.entities:
                if entity.type == "url":
                    extracted_url = text[entity.offset : entity.offset + entity.length]
                    if re.match(url_pattern, extracted_url):
                        url = extracted_url.rstrip(".,;!)]")
                        break
    if not url:
        match = re.search(url_pattern, text)
        if match:
            url = match.group(0).rstrip(".,;!)]")

    if not url:
        await message.reply_text("🔗 Please send a valid URL.", parse_mode="HTML")
        return

    use_web_search = context.user_data.get("web_search", False)
    use_url_context = context.user_data.get("url_context", False)

    task_data = (
        update.effective_chat.id,
        url,
        context,
        message,
        use_web_search,
        use_url_context,
        "one_paragraph_summary_V2",
    )
    await url_queue.put(task_data)
    print(f"URL added to queue: {url}. Queue size: {url_queue.qsize()}", flush=True)


@authorized
async def handle_qna_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles a user's question when they reply to a summary message.
    """
    message = update.message
    if not message.reply_to_message or not message.text:
        return

    # Check if the replied-to message is from our bot and contains a summary
    replied_message = message.reply_to_message
    if (
        not replied_message.from_user.is_bot
        or not replied_message.text
        or "Original Article" not in replied_message.text
    ):
        return

    # Extract URL from the replied message
    url = None
    if replied_message.entities:
        for entity in replied_message.entities:
            if entity.type == "text_link" and entity.url:
                # Check if this link corresponds to "Original Article"
                entity_text = replied_message.text[
                    entity.offset : entity.offset + entity.length
                ]
                if "Original Article" in entity_text:
                    url = entity.url
                    break
            elif entity.type == "url":
                # Plain URL
                url = replied_message.text[
                    entity.offset : entity.offset + entity.length
                ]
                # We prefer the "Original Article" link, but if we find a plain URL first/only, we might use it.
                # However, let's keep looking for the specific link if possible.
                # Actually, if we find a plain URL, it might be in the summary text.
                # But usually the Original Article link is a text_link.
                pass

    # If we didn't find the specific "Original Article" text_link, try to find ANY url
    if not url and replied_message.entities:
        for entity in replied_message.entities:
            if entity.type == "text_link" and entity.url:
                url = entity.url
                break
            elif entity.type == "url":
                url = replied_message.text[
                    entity.offset : entity.offset + entity.length
                ]
                break

    if not url:
        # Fallback: try regex on text just in case
        url_match = re.search(r"https?://[^\s<>\"'\[\]]+", replied_message.text)
        if url_match:
            url = url_match.group(0)

    if not url:
        return
    user_question = message.text
    chat_id = update.effective_chat.id

    # Show a loading message
    processing_message = await message.reply_text(
        "🤔 Thinking...",
        parse_mode="HTML",
        disable_notification=True,
    )
    stop_animation_event = asyncio.Event()
    animation_task = asyncio.create_task(
        animate_loading_message(
            context,
            chat_id,
            processing_message.message_id,
            stop_animation_event,
            fallback_mode=False,
        )
    )

    try:
        async with asyncio.timeout(300):  # 5 minutes timeout
            # 1. Re-scrape the article
            article_content, _, error_details = await scrape_article(url)
            if not article_content:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_message.message_id,
                    text=f"😥 <b>Could not re-fetch article content.</b>\n<pre>{error_details}</pre>",
                    parse_mode="HTML",
                )
                return

            # 2. Extract the previous summary text from the message
            # We'll just take the text before the "Original Article" link
            summary_text = replied_message.text.split("📖 Original Article")[0].strip()

            # 3. Call the new answer_question function
            default_model = (
                load_available_models()[0]
                if load_available_models()
                else "gemini-1.5-flash"
            )
            model_name = context.user_data.get("short_summary_model", default_model)

            answer_data = await answer_question(
                article=article_content,
                question=user_question,
                summary=summary_text,
                model_name=model_name,
            )

            stop_animation_event.set()
            await animation_task

            if not answer_data or "ERRORE:" in answer_data.get("summary", ""):
                error_message = answer_data.get("summary", "An unknown error occurred.")
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_message.message_id,
                    text=error_message,
                    parse_mode="HTML",
                )
                return

            # 4. Send the answer
            formatted_answer = telegramify_markdown.markdownify(
                answer_data["summary"], normalize_whitespace=False
            )
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_message.message_id,
                text=formatted_answer,
                parse_mode="MarkdownV2",
            )

    except TimeoutError:
        stop_animation_event.set()
        await animation_task
        print(f"Q&A processing timed out for: {url}", flush=True)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_message.message_id,
                text="⚠️ Request timed out. The operation took longer than 5 minutes. Please try again later.",
                parse_mode="HTML",
            )
        except TelegramError as te:
            print(
                f"Failed to send timeout message due to Telegram API error: {te}",
                flush=True,
            )

    except Exception as e:
        stop_animation_event.set()
        await animation_task
        print(f"Error in handle_qna_reply: {e}", flush=True)
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=processing_message.message_id,
            text=f"🤖 **ERROR:** Could not process the question.\nDetails: `{e}`",
            parse_mode="MarkdownV2",
        )
