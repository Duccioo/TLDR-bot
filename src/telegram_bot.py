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
from extractor import estrai_contenuto_da_url
from summarizer import summarize_article
from scraper import crea_articolo_telegraph_with_content

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit()

# States for conversation
CHOOSE_PROMPT = 1

# Define the keyboard layout
main_keyboard = [
    ["Scegli Prompt", "Quota API Gemini"],
]

# Get available prompts
prompt_files = [f.split(".")[0] for f in os.listdir("src/prompts") if f.endswith(".md")]
prompt_keyboard = [[prompt] for prompt in prompt_files]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to the summarizer bot! Send me a link to summarize.",
        reply_markup=reply_markup,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a help message when the /help command is issued."""
    await update.message.reply_text(
        "Send me a link to an article and I will summarize it for you. "
        "You can also use the keyboard to choose a different prompt or check the API quota."
    )

async def choose_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a prompt."""
    reply_markup = ReplyKeyboardMarkup(prompt_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Please choose a prompt for the summary:", reply_markup=reply_markup
    )
    return CHOOSE_PROMPT

async def prompt_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen prompt."""
    prompt = update.message.text
    context.user_data["prompt"] = prompt
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(f"Prompt set to: {prompt}", reply_markup=reply_markup)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Operation canceled.", reply_markup=reply_markup
    )
    return ConversationHandler.END

async def api_quota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a message about the API quota."""
    await update.message.reply_text(
        "To check your Gemini API quota, please visit the Google AI Studio."
    )

async def summarize_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Summarizes the content of a URL."""
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, update.message.text)
    if not match:
        await update.message.reply_text("Please send a valid URL.")
        return

    url = match.group(0)
    await update.message.reply_text("Processing the URL...")

    # Extract content
    article_content = estrai_contenuto_da_url(url)
    if not article_content:
        await update.message.reply_text("Could not extract content from the URL.")
        return

    # Generate one-paragraph summary
    one_paragraph_summary = summarize_article(
        article_content, summary_type="one_paragraph_summary"
    )

    # Generate technical summary with the chosen prompt
    technical_summary_prompt = context.user_data.get("prompt", "technical_summary")
    technical_summary = summarize_article(
        article_content, summary_type=technical_summary_prompt
    )

    # Create Telegraph page with the technical summary
    if technical_summary:
        telegraph_url = crea_articolo_telegraph_with_content(
            title=article_content.title or "Summary",
            content=technical_summary,
            author_name=article_content.author or "Summarizer Bot",
        )
    else:
        telegraph_url = None

    if one_paragraph_summary and telegraph_url:
        await update.message.reply_text(
            f"Here is a summary:\n\n{one_paragraph_summary}\n\n"
            f"Read the full summary here: {telegraph_url}"
        )
    else:
        await update.message.reply_text("Could not generate the summary.")


def main():
    """Main function to run the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add conversation handler for choosing a prompt
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Scegli Prompt$"), choose_prompt_start)],
        states={
            CHOOSE_PROMPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, prompt_chosen)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Add handler for API quota
    application.add_handler(MessageHandler(filters.Regex("^Quota API Gemini$"), api_quota))

    # on non command i.e message - summarize the URL
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, summarize_url))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()
    print("Bot is running...")

if __name__ == "__main__":
    main()
