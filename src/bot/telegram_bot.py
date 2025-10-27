"""
Telegram bot to interact with the summarizer.
"""

import os
import re
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Import functions from other modules
from core.extractor import estrai_contenuto_da_url
from core.summarizer import summarize_article
from core.scraper import crea_articolo_telegraph_with_content
from core.quota_manager import get_quota_summary

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit()

# States for conversation
CHOOSE_PROMPT, CHOOSE_MODEL = 1, 2

# Define the keyboard layout
main_keyboard = [
    ["Scegli Prompt", "Cambia Modello"],
    ["Web Search On/Off", "URL Context On/Off"],
    ["Quota API Gemini"],
]

# Define available models
models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
model_keyboard = [[model] for model in models]

# Get available prompts
prompt_files = [f.split(".")[0] for f in os.listdir("src/bot/prompts") if f.endswith(".md")]
prompt_keyboard = [[prompt] for prompt in prompt_files]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    context.user_data["web_search"] = False
    context.user_data["url_context"] = False
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "<b>Benvenuto nel bot riassuntore!</b> Inviami un link per iniziare.",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a help message when the /help command is issued."""
    await update.message.reply_text(
        "Inviami un link a un articolo e io lo riassumerò per te.\n"
        "Usa la tastiera per scegliere un prompt diverso o controllare le quote API.",
        parse_mode="HTML",
    )

async def toggle_web_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles web search on or off."""
    context.user_data["web_search"] = not context.user_data.get("web_search", False)
    status = "attiva" if context.user_data["web_search"] else "disattiva"
    await update.message.reply_text(f"Ricerca web <b>{status}</b>.", parse_mode="HTML")

async def toggle_url_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles URL context on or off."""
    context.user_data["url_context"] = not context.user_data.get("url_context", False)
    status = "attivo" if context.user_data["url_context"] else "disattivo"
    await update.message.reply_text(f"Contesto URL <b>{status}</b>.", parse_mode="HTML")

async def choose_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a prompt."""
    reply_markup = ReplyKeyboardMarkup(prompt_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Scegli un prompt per il riassunto:", reply_markup=reply_markup, parse_mode="HTML"
    )
    return CHOOSE_PROMPT

async def prompt_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen prompt."""
    prompt = update.message.text
    context.user_data["prompt"] = prompt
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Prompt impostato su: <b>{prompt}</b>", reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Operation canceled.", reply_markup=reply_markup
    )
    return ConversationHandler.END

async def choose_model_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a model."""
    reply_markup = ReplyKeyboardMarkup(model_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Scegli un modello per il riassunto:", reply_markup=reply_markup, parse_mode="HTML"
    )
    return CHOOSE_MODEL

async def model_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen model."""
    model = update.message.text
    context.user_data["model"] = model
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Modello impostato su: <b>{model}</b>", reply_markup=reply_markup, parse_mode="HTML")
    return ConversationHandler.END

async def api_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a summary of the API quota usage."""
    summary = get_quota_summary()
    await update.message.reply_text(summary, parse_mode="HTML")

async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarizes the content of a URL."""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, update.message.text)
    if not match:
        await update.message.reply_text("Per favore, invia un URL valido.", parse_mode="HTML")
        return

    url = match.group(0)
    await update.message.reply_text("Elaborazione dell'URL in corso...", parse_mode="HTML")

    # Extract content
    article_content = estrai_contenuto_da_url(url)
    if not article_content:
        await update.message.reply_text("Impossibile estrarre il contenuto dall'URL.", parse_mode="HTML")
        return

    # Get user choices from context
    model_name = context.user_data.get("model", "gemini-1.5-flash")
    use_web_search = context.user_data.get("web_search", False)
    use_url_context = context.user_data.get("url_context", False)
    technical_summary_prompt = context.user_data.get("prompt", "technical_summary")

    # Generate summaries
    one_paragraph_summary_data = summarize_article(
        article_content,
        summary_type="one_paragraph_summary",
        model_name=model_name,
        use_web_search=use_web_search,
        use_url_context=use_url_context,
    )
    technical_summary_data = summarize_article(
        article_content,
        summary_type=technical_summary_prompt,
        model_name=model_name,
        use_web_search=use_web_search,
        use_url_context=use_url_context,
    )

    one_paragraph_summary = one_paragraph_summary_data.get("summary")
    technical_summary = technical_summary_data.get("summary")
    image_urls = technical_summary_data.get("images")

    # Create Telegraph page
    if technical_summary:
        telegraph_url = crea_articolo_telegraph_with_content(
            title=article_content.title or "Summary",
            content=technical_summary,
            author_name=article_content.author or "Summarizer Bot",
            image_urls=image_urls,
        )
    else:
        telegraph_url = None

    if one_paragraph_summary and telegraph_url:
        await update.message.reply_text(
            f"<b>Ecco un riassunto:</b>\n\n{one_paragraph_summary}\n\n"
            f"<a href='{telegraph_url}'>Leggi il riassunto completo qui</a>",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text("Impossibile generare il riassunto.", parse_mode="HTML")


def main():
    """Main function to run the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add conversation handler for choosing a prompt
    prompt_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Scegli Prompt$"), choose_prompt_start)],
        states={
            CHOOSE_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_chosen)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(prompt_conv_handler)

    # Add conversation handler for choosing a model
    model_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Cambia Modello$"), choose_model_start)],
        states={
            CHOOSE_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, model_chosen)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(model_conv_handler)

    # Add handler for API quota
    application.add_handler(MessageHandler(filters.Regex("^Quota API Gemini$"), api_quota))

    # Add handlers for toggling features
    application.add_handler(MessageHandler(filters.Regex("^Web Search On/Off$"), toggle_web_search))
    application.add_handler(MessageHandler(filters.Regex("^URL Context On/Off$"), toggle_url_context))

    # on non command i.e message - summarize the URL
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_url))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    print("Bot is running...")

if __name__ == "__main__":
    main()
