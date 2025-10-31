"""
Main Telegram bot application.
"""

import sys
import signal
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

from config import (
    TELEGRAM_BOT_TOKEN,
    CHOOSE_PROMPT,
    CHOOSE_MODEL,
    AUTH,
    SELECT_SHORT_SUMMARY_MODEL,
    SELECT_TELEGRAPH_SUMMARY_MODEL,
)
from handlers.auth_handlers import start, check_password, cancel_auth
from handlers.command_handlers import (
    help_command,
    api_quota,
    toggle_web_search,
    toggle_url_context,
)
from handlers.conversation_handlers import (
    choose_prompt_start,
    prompt_chosen,
    choose_model_start,
    model_selection_submenu,
    short_summary_model_chosen,
    telegraph_summary_model_chosen,
    cancel,
)
from handlers.message_handlers import summarize_url
from handlers.callback_handlers import generate_telegraph_page


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n✓ Shutting down bot (Ctrl+C pressed)...", flush=True)
    sys.exit(0)


def setup_handlers(application: Application):
    """Setup all bot handlers."""

    # Add authentication handler
    auth_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel_auth)],
    )
    application.add_handler(auth_handler)

    # Add command handlers
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
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, model_selection_submenu
                )
            ],
            SELECT_SHORT_SUMMARY_MODEL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, short_summary_model_chosen
                )
            ],
            SELECT_TELEGRAPH_SUMMARY_MODEL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, telegraph_summary_model_chosen
                )
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

    # Add handler for URL messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_url)
    )

    # Add callback handler for Telegraph page creation
    application.add_handler(
        CallbackQueryHandler(generate_telegraph_page, pattern="^create_telegraph_page$")
    )


def main():
    """Main function to run the bot."""
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize quota.json file if it doesn't exist
    from core.quota_manager import get_quota_data

    print("🔍 Verifica esistenza file quota.json...")
    get_quota_data()  # This will create the file if it doesn't exist

    print(f"Initializing bot with token: {TELEGRAM_BOT_TOKEN[:10]}...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    print("Adding handlers...")
    setup_handlers(application)

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
