"""
Main entry point for the Telegram summarizer bot.
"""
import os
import sys
import signal
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from functools import partial

# --- Path and Environment Setup ---
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from src import handlers, ui, utils
from src.utils import authorized

# --- Main Bot Logic ---
def main():
    """Sets up and runs the Telegram bot."""
    # --- Environment Variables ---
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot_password = os.getenv("BOT_PASSWORD")
    if not telegram_bot_token:
        sys.exit("Error: TELEGRAM_BOT_TOKEN not set.")

    # --- UI Setup ---
    prompts_path = ROOT_DIR / "src" / "prompts"
    data_path = ROOT_DIR / "src" / "data" / "quota.json"
    prompt_keyboard = ui.load_available_prompts(prompts_path)
    model_keyboard = ui.load_available_models(data_path)

    # --- Application Setup ---
    app = Application.builder().token(telegram_bot_token).build()

    # Create a partial for the authorized decorator to pass the password
    auth_decorator = authorized(bot_password)

    # --- Conversation Handler ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", partial(handlers.start, bot_password=bot_password))],
        states={
            handlers.AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, partial(handlers.check_password, bot_password=bot_password))],
            handlers.CHOOSE_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.prompt_chosen)],
            handlers.CHOOSE_MODEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.model_chosen)],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)],
    )

    # --- Handlers ---
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", auth_decorator(handlers.help_command)))
    app.add_handler(MessageHandler(filters.Regex("^📝 Scegli Prompt$"), auth_decorator(partial(handlers.choose_prompt_start, prompt_keyboard=prompt_keyboard))))
    app.add_handler(MessageHandler(filters.Regex("^🤖 Cambia Modello$"), auth_decorator(partial(handlers.choose_model_start, model_keyboard=model_keyboard))))
    app.add_handler(MessageHandler(filters.Regex("^📊 Quota API Gemini$"), auth_decorator(handlers.api_quota)))
    app.add_handler(MessageHandler(filters.Regex("^🌐 Web Search On/Off$"), auth_decorator(handlers.toggle_web_search)))
    app.add_handler(MessageHandler(filters.Regex("^🔗 URL Context On/Off$"), auth_decorator(handlers.toggle_url_context)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auth_decorator(handlers.summarize_url)))
    app.add_handler(CallbackQueryHandler(auth_decorator(handlers.generate_telegraph_page), pattern="^create_telegraph_page$"))

    # --- Start Bot ---
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
