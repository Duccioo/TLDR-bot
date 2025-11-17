"""
Keyboard layouts for the Telegram bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import load_available_models, load_available_prompts


def get_retry_keyboard(
    url: str, summary_type: str, use_web_search: bool, use_url_context: bool
):
    """Returns the retry keyboard layout."""
    callback_data = (
        f"retry:{summary_type}:{url}:{use_web_search}:{use_url_context}"
    )
    keyboard = [[InlineKeyboardButton("🔄 Retry", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def get_main_keyboard():
    """Returns the main keyboard layout."""
    keyboard = [
        ["📝 Choose Prompt", "🤖 Change Model"],
        ["🌐 Web Search On/Off", "🔗 URL Context On/Off"],
        ["📊 Gemini API Quota"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_model_keyboard():
    """Returns the model selection keyboard."""
    models = load_available_models()
    keyboard = [[model] for model in models]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_model_selection_submenu_keyboard(context):
    """Returns the model selection submenu keyboard."""
    user_data = context.user_data
    default_model = (
        load_available_models()[0] if load_available_models() else "gemini-2.5-flash"
    )

    short_summary_model = user_data.get("short_summary_model", default_model)
    telegraph_summary_model = user_data.get("telegraph_summary_model", default_model)

    keyboard = [
        [f"📄 Short summary model: {short_summary_model}"],
        [f"📝 Telegraph page model: {telegraph_summary_model}"],
        ["⬅️ Back to main menu"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_prompt_keyboard():
    """Returns the prompt selection keyboard."""
    prompts = load_available_prompts()
    keyboard = [[prompt] for prompt in prompts]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
