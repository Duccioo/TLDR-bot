"""
Conversation handlers for the Telegram bot.
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from decorators import authorized
from keyboards import (
    get_main_keyboard,
    get_prompt_keyboard,
    get_model_keyboard,
    get_model_selection_submenu_keyboard,
)
from config import (
    CHOOSE_PROMPT,
    CHOOSE_MODEL,
    SELECT_SHORT_SUMMARY_MODEL,
    SELECT_TELEGRAPH_SUMMARY_MODEL,
)


@authorized
async def model_selection_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the model selection submenu."""
    text = update.message.text
    if text.startswith("📄 Short summary model:"):
        reply_markup = get_model_keyboard()
        await update.message.reply_text(
            "🤖 Choose a model for the short summary:",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return SELECT_SHORT_SUMMARY_MODEL
    elif text.startswith("📝 Telegraph page model:"):
        reply_markup = get_model_keyboard()
        await update.message.reply_text(
            "🤖 Choose a model for the Telegraph page:",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return SELECT_TELEGRAPH_SUMMARY_MODEL
    elif text == "⬅️ Back to main menu":
        reply_markup = get_main_keyboard()
        await update.message.reply_text(
            "⬅️ Returning to the main menu.",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
        return ConversationHandler.END
    return CHOOSE_MODEL


@authorized
async def short_summary_model_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen model for the short summary."""
    model = update.message.text
    context.user_data["short_summary_model"] = model
    reply_markup = get_model_selection_submenu_keyboard(context)
    await update.message.reply_text(
        f"👍 Short summary model set to: <b>{model}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return CHOOSE_MODEL


@authorized
async def telegraph_summary_model_chosen(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Stores the chosen model for the Telegraph page."""
    model = update.message.text
    context.user_data["telegraph_summary_model"] = model
    reply_markup = get_model_selection_submenu_keyboard(context)
    await update.message.reply_text(
        f"👍 Telegraph page model set to: <b>{model}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return CHOOSE_MODEL


@authorized
async def choose_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a prompt."""
    reply_markup = get_prompt_keyboard()
    await update.message.reply_text(
        "📝 Choose a prompt for the summary:",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return CHOOSE_PROMPT


@authorized
async def prompt_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the chosen prompt."""
    prompt = update.message.text
    context.user_data["prompt"] = prompt
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        f"👍 Prompt set to: <b>{prompt}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return ConversationHandler.END


@authorized
async def choose_model_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a model."""
    reply_markup = get_model_selection_submenu_keyboard(context)
    await update.message.reply_text(
        "🤖 Choose which model to edit:",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return CHOOSE_MODEL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        "❌ Operation cancelled.", reply_markup=reply_markup
    )
    return ConversationHandler.END
