"""
Keyboard layouts for the Telegram bot.
"""

from telegram import ReplyKeyboardMarkup
from config import load_available_models, load_available_prompts


def get_main_keyboard():
    """Returns the main keyboard layout."""
    keyboard = [
        ["📝 Scegli Prompt", "🤖 Cambia Modello"],
        ["🌐 Web Search On/Off", "🔗 URL Context On/Off"],
        ["📊 Quota API Gemini"],
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
    default_model = load_available_models()[0] if load_available_models() else "gemini-2.5-flash"

    short_summary_model = user_data.get("short_summary_model", default_model)
    telegraph_summary_model = user_data.get("telegraph_summary_model", default_model)

    keyboard = [
        [f"📄 Modello riassunto breve: {short_summary_model}"],
        [f"📝 Modello pagina Telegraph: {telegraph_summary_model}"],
        ["⬅️ Torna al menu principale"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_prompt_keyboard():
    """Returns the prompt selection keyboard."""
    prompts = load_available_prompts()
    keyboard = [[prompt] for prompt in prompts]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
