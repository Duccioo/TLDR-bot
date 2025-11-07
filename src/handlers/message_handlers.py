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
from utils import format_summary_text, clean_hashtags_format
from config import TITLE_EMOJIS, load_available_models


async def animate_loading_message(
    context, chat_id, message_id, stop_event, fallback_mode=False
):
    """
    Anima un messaggio di caricamento.
    Usa emoji di orologio di default o una sequenza "arrabbiata" in modalità fallback.
    """
    base_text = "Elaborazione in corso"
    dots = ""

    if fallback_mode:
        emojis = ["😊", "😐", "😠", "😡"]
        base_text = "Estrazione standard fallita, uso il metodo alternativo"
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

        # Aggiorna l'indice dell'emoji
        if fallback_mode:
            # L'animazione arrabbiata progredisce fino all'ultimo emoji e si ferma lì
            if emoji_index < len(emojis) - 1:
                emoji_index += 1
        else:
            # L'animazione dell'orologio va in loop
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
                print("Animazione interrotta: messaggio non trovato.")
                break
            # Non loggare l'errore se il messaggio è identico, è normale
            if "Message is not modified" not in str(e):
                print(f"Errore durante l'animazione: {e}")

        await asyncio.sleep(0.8 if fallback_mode else 0.5)


@authorized
async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarizes the content of a URL."""
    url = None

    if update.message.entities:
        for entity in update.message.entities:
            if entity.type == "url":
                url = update.message.text[entity.offset : entity.offset + entity.length]
                break
            elif entity.type == "text_link":
                url = entity.url
                break

    if not url:
        url_pattern = r"https?://[^\s<>\"']+"
        match = re.search(url_pattern, update.message.text)
        if match:
            url = match.group(0).rstrip(".,;!)")

    if not url:
        try:
            await update.message.reply_text(
                "🔗 Per favore, invia un URL valido.", parse_mode="HTML"
            )
        except NetworkError as e:
            print(f"Errore di rete nell'invio del messaggio di URL non valido: {e}")
        return

    try:
        processing_message = await update.message.reply_text(
            "⏳ Elaborazione dell'URL in corso...",
            parse_mode="HTML",
            disable_notification=True,
        )
    except NetworkError as e:
        print(f"Errore di rete nell'invio del messaggio di elaborazione: {e}")
        return  # Interrompi se non possiamo nemmeno inviare il messaggio iniziale

    stop_animation_event = asyncio.Event()
    animation_task = None  # Inizializza a None

    try:
        # Esegui lo scraping e ottieni il contenuto e lo stato del fallback
        article_content, fallback_used = await scrape_article(url)

        # Avvia l'animazione DOPO aver determinato se usare il fallback
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
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=processing_message.message_id,
                    text="😥 Impossibile estrarre il contenuto dall'URL.",
                    parse_mode="HTML",
                )
            except NetworkError as e:
                print(
                    f"Errore di rete nel tentativo di aggiornare il messaggio di errore scraping: {e}"
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

        # Genera il riassunto
        one_paragraph_summary_data = await summarize_article(
            article_content,
            "one_paragraph_summary_V2",
            model_name=model_name,
            use_web_search=use_web_search,
            use_url_context=use_url_context,
        )

        if not one_paragraph_summary_data:
            raise ValueError("Impossibile generare il riassunto.")

        one_paragraph_summary = one_paragraph_summary_data.get("summary")
        context.user_data["articles"][article_id][
            "one_paragraph_summary"
        ] = one_paragraph_summary

        formatted_summary = format_summary_text(one_paragraph_summary)
        summary_body, hashtags_line = clean_hashtags_format(formatted_summary)

        article_title = article_content.title or "Articolo"

        message_sections = [f"**{random_emoji} {article_title}**"]
        if hashtags_line:
            message_sections.append(hashtags_line)
        if summary_body:
            message_sections.append(summary_body)
        message_sections.append(f"\n_Riassunto generato con {model_name}_")

        message_markdown = "\n\n".join(
            section for section in message_sections if section
        )

        telegram_message = telegramify_markdown.markdownify(
            message_markdown,
            normalize_whitespace=False,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📄 Crea pagina Telegraph",
                    callback_data=f"create_telegraph_page:{article_id}",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if animation_task:
            stop_animation_event.set()
            await animation_task

        try:
            # Elimina il messaggio di processing
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
            )
            # Invia il riassunto come risposta al messaggio originale dell'utente
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=telegram_message,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2",
                reply_to_message_id=update.message.message_id,
            )
        except NetworkError as e:
            print(f"Errore di rete nell'invio del riassunto finale: {e}")

    except NetworkError as e:
        print(f"Errore di rete non gestito durante il processo di riassunto: {e}")
        if animation_task and not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task

    except Exception as e:
        if animation_task and not stop_animation_event.is_set():
            stop_animation_event.set()
            await animation_task

        print(f"Errore imprevisto durante il riassunto: {e}")
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id,
                text=f"🤖 ERRORE: Impossibile completare la richiesta.\nDettagli: {e}",
                parse_mode="HTML",
            )
        except NetworkError as ne:
            print(
                f"Errore di rete nel tentativo di inviare un messaggio di errore finale: {ne}"
            )
