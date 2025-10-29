"""
UI constants and keyboard layouts for the bot.
"""
from pathlib import Path
import json

# --- Constants ---
main_keyboard = [
    ["📝 Scegli Prompt", "🤖 Cambia Modello"],
    ["🌐 Web Search On/Off", "🔗 URL Context On/Off"],
    ["📊 Quota API Gemini"],
]

TITLE_EMOJIS = ["📰", "📄", "💡", "✨", "🚀", "🎯"]

# --- Dynamic Keyboards ---
def load_available_models(data_path: Path) -> list[list[str]]:
    """Loads model names from quota.json for the keyboard."""
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            models = list(json.load(f).get("gemini", {}).keys())
            return [[model] for model in models]
    except (FileNotFoundError, json.JSONDecodeError):
        return [["gemini-2.5-flash"], ["gemini-2.0-flash"]]

def load_available_prompts(prompts_path: Path) -> list[list[str]]:
    """Loads prompt names from the prompts directory for the keyboard."""
    return [[prompt.stem] for prompt in prompts_path.glob("*.md")]
