"""
Conversation handlers for the Telegram bot.
"""

from telegram import Update
from telegram.ext import ContextTypes
from decorators import authorized
from keyboards import get_main_keyboard, get_prompt_keyboard, get_model_keyboard
from config import CHOOSE_PROMPT, CHOOSE_MODEL


@authorized
async def choose_prompt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a prompt."""
    reply_markup = get_prompt_keyboard()
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
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        f"👍 Prompt impostato su: <b>{prompt}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return -1  # ConversationHandler.END


@authorized
async def choose_model_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation to choose a model."""
    reply_markup = get_model_keyboard()
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
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        f"👍 Modello impostato su: <b>{model}</b>",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    return -1  # ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels the conversation."""
    reply_markup = get_main_keyboard()
    await update.message.reply_text(
        "❌ Operazione annullata.", reply_markup=reply_markup
    )
    return -1  # ConversationHandler.END
