"""
Telegram bot to interact with the summarizer.
"""

import os
import re
import json
import sys
import signal
from functools import wraps
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
BOT_PASSWORD = os.getenv("BOT_PASSWORD")
PROMPTS_FOLDER = os.path.join("src", "prompts")


if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit()

# In-memory storage for authorized user IDs
AUTHORIZED_USERS = []

# States for conversation
CHOOSE_PROMPT, CHOOSE_MODEL, AUTH = 1, 2, 3

# Define the keyboard layout with emojis
main_keyboard = [
    ["📝 Scegli Prompt", "🤖 Cambia Modello"],
    ["🌐 Web Search On/Off", "🔗 URL Context On/Off"],
    ["📊 Quota API Gemini"],
]


# Load available models from quota.json
def load_available_models():
    """Load available models from quota.json file."""
    quota_file_path = "src/data/quota.json"
    try:
        with open(quota_file_path, "r", encoding="utf-8") as f:
            quota_data = json.load(f)
            # Extract model names from the gemini section
            available_models = list(quota_data.get("gemini", {}).keys())
            return available_models
    except FileNotFoundError:
        print(f"Warning: {quota_file_path} not found. Using default models.")
        return ["gemini-2.5-flash", "gemini-2.0-flash"]
    except json.JSONDecodeError:
        print(f"Warning: Error parsing {quota_file_path}. Using default models.")
        return ["gemini-2.5-flash", "gemini-2.0-flash"]


# Define available models from quota.json
models = load_available_models()
model_keyboard = [[model] for model in models]

# Get available prompts
prompt_files = [
    f.split(".")[0] for f in os.listdir(PROMPTS_FOLDER) if f.endswith(".md")
]
prompt_keyboard = [[prompt] for prompt in prompt_files]


def is_authorized(user_id):
    """Checks if a user is authorized."""
    # If no password is set, everyone is authorized
    if not BOT_PASSWORD:
        return True
    return user_id in AUTHORIZED_USERS


def authorized(func):
    """Decorator to check if a user is authorized."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_authorized(user_id):
            await update.message.reply_text(
                "⛔ Non sei autorizzato. Per favore, usa /start per autenticarti.",
                parse_mode="HTML",
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    user_id = update.effective_user.id
    print(f"Received /start command from user {user_id}")

    if not is_authorized(user_id):
        await update.message.reply_text(
            "🔐 Questo bot è protetto da password. Per favore, inserisci la password per continuare:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML",
        )
        return AUTH

    context.user_data["web_search"] = False
    context.user_data["url_context"] = False
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 <b>Benvenuto nel bot riassuntore!</b> Inviami un link per iniziare.",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    print("Welcome message sent successfully")
    return ConversationHandler.END


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the password entered by the user."""
    password = update.message.text
    user_id = update.effective_user.id

    if password == BOT_PASSWORD:
        AUTHORIZED_USERS.append(user_id)
        print(f"User {user_id} authorized successfully.")
        context.user_data["web_search"] = False
        context.user_data["url_context"] = False
        reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "<b>Accesso consentito!</b> ✅ Ora puoi usare il bot. Inviami un link per iniziare.",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return ConversationHandler.END
    else:
        print(f"User {user_id} entered wrong password.")
        await update.message.reply_text("⛔ Password errata. Riprova.", parse_mode="HTML")
        return AUTH


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
    await update.message.reply_text(f"🌐 Ricerca web <b>{status}</b>.", parse_mode="HTML")


@authorized
async def toggle_url_context(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggles URL context on or off."""
    context.user_data["url_context"] = not context.user_data.get("url_context", False)
    status = "attivo" if context.user_data["url_context"] else "disattivo"
    await update.message.reply_text(f"🔗 Contesto URL <b>{status}</b>.", parse_mode="HTML")


@authorized
async def choose_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a prompt."""
    reply_markup = ReplyKeyboardMarkup(prompt_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📝 Scegli un prompt per il riassunto:",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return CHOOSE_PROMPT


@authorized
async def prompt_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen prompt."""
    prompt = update.message.text
    context.user_data["prompt"] = prompt
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👍 Prompt impostato su: <b>{prompt}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text("❌ Operazione annullata.", reply_markup=reply_markup)
    return ConversationHandler.END


async def cancel_auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the authentication process."""
    await update.message.reply_text("❌ Autenticazione annullata. Usa /start per riprovare.")
    return ConversationHandler.END


@authorized
async def choose_model_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a model."""
    reply_markup = ReplyKeyboardMarkup(model_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 Scegli un modello per il riassunto:",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return CHOOSE_MODEL


@authorized
async def model_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen model."""
    model = update.message.text
    context.user_data["model"] = model
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"👍 Modello impostato su: <b>{model}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return ConversationHandler.END


@authorized
async def api_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a summary of the API quota usage."""
    summary = get_quota_summary()
    await update.message.reply_text(f"📊 <b>Quota API Gemini</b> 📊\n\n{summary}", parse_mode="HTML")


@authorized
async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarizes the content of a URL."""
    url_pattern = r"https?://[^\s]+"
    match = re.search(url_pattern, update.message.text)
    if not match:
        await update.message.reply_text(
            "🔗 Per favore, invia un URL valido.", parse_mode="HTML"
        )
        return

    url = match.group(0)
    await update.message.reply_text(
        "⏳ Elaborazione dell'URL in corso...", parse_mode="HTML"
    )

    # Extract content
    article_content = estrai_contenuto_da_url(url)
    if not article_content:
        await update.message.reply_text(
            "😥 Impossibile estrarre il contenuto dall'URL.", parse_mode="HTML"
        )
        return

    # Get user choices from context
    model_name = context.user_data.get("model", "gemini-2.5-flash")
    use_web_search = context.user_data.get("web_search", False)
    use_url_context = context.user_data.get("url_context", False)
    technical_summary_prompt = context.user_data.get("prompt", "technical_summary")

    # Generate summaries
    try:
        print("Generating one paragraph summary...", flush=True)
        one_paragraph_summary_data = summarize_article(
            article_content,
            summary_type="one_paragraph_summary",
            model_name=model_name,
            use_web_search=use_web_search,
            use_url_context=use_url_context,
        )
        print("One paragraph summary done!", flush=True)

        print("Generating technical summary...", flush=True)
        technical_summary_data = summarize_article(
            article_content,
            summary_type=technical_summary_prompt,
            model_name=model_name,
            use_web_search=use_web_search,
            use_url_context=use_url_context,
        )
        print("Technical summary done!", flush=True)
    except Exception as e:
        print(f"Error during summarization: {e}", flush=True)
        await update.message.reply_text(
            "🤖 Si è verificato un errore durante la generazione del riassunto.",
            parse_mode="HTML",
        )
        return

    print("Checking summary data...", flush=True)
    if not one_paragraph_summary_data or not technical_summary_data:
        print("Summary data is None!", flush=True)
        await update.message.reply_text(
            "😥 Impossibile generare il riassunto. Verifica che i file prompt esistano.",
            parse_mode="HTML",
        )
        return

    one_paragraph_summary = one_paragraph_summary_data.get("summary")
    technical_summary = technical_summary_data.get("summary")
    image_urls = technical_summary_data.get("images")

    print(f"One paragraph summary: {bool(one_paragraph_summary)}", flush=True)
    print(f"Technical summary: {bool(technical_summary)}", flush=True)
    print(f"Image URLs: {image_urls}")

    # Create Telegraph page
    if technical_summary:
        print("Creating Telegraph page...")
        telegraph_url = crea_articolo_telegraph_with_content(
            title=article_content.title or "Summary",
            content=technical_summary,
            author_name=article_content.author or "Summarizer Bot",
            image_urls=image_urls,
        )
        print(f"Telegraph URL: {telegraph_url}")
    else:
        print("No technical summary, skipping Telegraph page creation")
        telegraph_url = None

    print(
        f"Checking conditions: one_paragraph={bool(one_paragraph_summary)}, telegraph={bool(telegraph_url)}"
    )

    if one_paragraph_summary and telegraph_url:
        print("Sending complete summary...")
        await update.message.reply_text(
            f"📰 <b>Ecco un riassunto:</b>\n\n{one_paragraph_summary}\n\n"
            f"📄 <a href='{telegraph_url}'>Leggi il riassunto completo qui</a>",
            parse_mode="HTML",
        )
        print("Summary sent successfully!")
    else:
        print("Sending error message...")
        await update.message.reply_text(
            "😥 Impossibile generare il riassunto.", parse_mode="HTML"
        )
        print("Error message sent")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n✓ Shutting down bot (Ctrl+C pressed)...", flush=True)
    sys.exit(0)


def main():
    """Main function to run the bot."""
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print(f"Initializing bot with token: {TELEGRAM_BOT_TOKEN[:10]}...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    print("Adding handlers...")

    # Add authentication handler
    auth_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel_auth)],
    )
    application.add_handler(auth_handler)

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("help", help_command))

    # Add conversation handler for choosing a prompt
    prompt_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📝 Scegli Prompt$"), choose_prompt_start)
        ],
        states={
            CHOOSE_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_chosen)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(prompt_conv_handler)

    # Add conversation handler for choosing a model
    model_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🤖 Cambia Modello$"), choose_model_start)
        ],
        states={
            CHOOSE_MODEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, model_chosen)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(model_conv_handler)

    # Add handler for API quota
    application.add_handler(
        MessageHandler(filters.Regex("^📊 Quota API Gemini$"), api_quota)
    )

    # Add handlers for toggling features
    application.add_handler(
        MessageHandler(filters.Regex("^🌐 Web Search On/Off$"), toggle_web_search)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^🔗 URL Context On/Off$"), toggle_url_context)
    )

    # on non command i.e message - summarize the URL
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_url)
    )

    # Run the bot until the user presses Ctrl-C
    print("Bot is starting...")
    print("Connecting to Telegram servers...")
    print("Waiting for messages... (send /start to your bot to test)")
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
    except KeyboardInterrupt:
        print("\n✓ Bot stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"✗ Error running bot: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("Shutting down...")


if __name__ == "__main__":
    main()
