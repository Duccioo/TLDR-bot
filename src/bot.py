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
import asyncio
from handlers.message_handlers import (
    summarize_url,
    url_processor_worker,
    handle_qna_reply,
)
from handlers.callback_handlers import (
    generate_telegraph_page,
    retry_hashtags,
    retry_summary,
    save_to_linkwarden,
)


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
            MessageHandler(filters.Regex("^📝 Choose Prompt$"), choose_prompt_start)
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
            MessageHandler(filters.Regex("^🤖 Change Model$"), choose_model_start)
        ],
        states={
            CHOOSE_MODEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, model_selection_submenu)
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
    application.add_handler(MessageHandler(filters.Regex("^📊 API Quota$"), api_quota))

    # Add handlers for toggling features
    application.add_handler(
        MessageHandler(filters.Regex("^🌐 Web Search On/Off$"), toggle_web_search)
    )
    application.add_handler(
        MessageHandler(filters.Regex("^🔗 URL Context On/Off$"), toggle_url_context)
    )

    # Add callback handlers BEFORE the generic message handler
    # Add callback handler for Telegraph page creation
    application.add_handler(
        CallbackQueryHandler(generate_telegraph_page, pattern="^create_telegraph_page:")
    )
    # Add callback handler for retrying hashtags
    application.add_handler(
        CallbackQueryHandler(retry_hashtags, pattern="^retry_hashtags:")
    )
    # Add callback handler for saving to LinkWarden
    application.add_handler(
        CallbackQueryHandler(save_to_linkwarden, pattern="^save_to_linkwarden:")
    )
    # Add callback handler for retrying the whole summary
    application.add_handler(CallbackQueryHandler(retry_summary, pattern="^retry:"))

    # Add the Q&A reply handler. This specifically looks for replies.
    application.add_handler(
        MessageHandler(
            filters.REPLY & filters.TEXT & ~filters.COMMAND, handle_qna_reply
        )
    )

    # Add handler for URL messages (MUST be last to avoid catching everything)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_url)
    )


async def post_init_hook(application: Application):
    """
    This function will be called after the Application is initialized.
    It's the perfect place to start background tasks.
    """
    print("Starting URL processor worker...", flush=True)
    asyncio.create_task(url_processor_worker())


def main():
    """Main function to run the bot."""
    # Setup signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize quota.json file if it doesn't exist
    from core.quota_manager import get_quota_data, sync_models

    print("🔍 Verifica esistenza file quota.json...")
    get_quota_data()  # This will create the file if it doesn't exist

    print("🔄 Sincronizzazione modelli dai provider...")
    sync_models()

    print(f"Initializing bot with token: {TELEGRAM_BOT_TOKEN[:10]}...")
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init_hook)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

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
            bootstrap_retries=-1,
            timeout=30,
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
