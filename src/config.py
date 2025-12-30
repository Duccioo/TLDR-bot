"""
Configuration and constants for the Telegram bot.
"""

import os
import pathlib
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the Telegram bot token from the environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")
SUMMARY_LANGUAGE = os.getenv("SUMMARY_LANGUAGE", "English")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Paths
PROMPTS_FOLDER = os.path.join("src", "prompts")
QUOTA_FILE_PATH = os.path.join("src", "data", "quota.json")

# Conversation states
(
    CHOOSE_PROMPT,
    CHOOSE_MODEL,
    AUTH,
    SELECT_SHORT_SUMMARY_MODEL,
    SELECT_TELEGRAPH_SUMMARY_MODEL,
) = range(5)

# List of random emojis for article titles
TITLE_EMOJIS = [
    "📰",
    "📄",
    "📃",
    "📑",
    "📚",
    "📖",
    "📝",
    "✍️",
    "📌",
    "🔖",
    "💡",
    "🌟",
    "⭐",
    "✨",
    "🎯",
    "🎓",
    "🧠",
    "💭",
    "🔍",
    "🔎",
    "🚀",
    "🎨",
    "🎭",
    "🎪",
    "🎬",
    "🎵",
    "🎸",
    "🏆",
    "🎁",
    "🎉",
]


def load_available_models():
    """Load available models from quota.json file."""
    try:
        with open(QUOTA_FILE_PATH, "r", encoding="utf-8") as f:
            quota_data = json.load(f)
            models = []

            # Gemini
            for m in quota_data.get("gemini", {}).keys():
                models.append(f"Gemini: {m}")

            # Groq
            if GROQ_API_KEY:
                for m in quota_data.get("groq", {}).keys():
                    models.append(f"Groq: {m}")

            # OpenRouter
            if OPENROUTER_API_KEY:
                for m in quota_data.get("openrouter", {}).keys():
                    models.append(f"OpenRouter: {m}")

            return models
    except FileNotFoundError:
        print(f"Warning: {QUOTA_FILE_PATH} not found. Using default models.")
        return ["gemini-2.5-flash", "gemini-2.0-flash"]
    except json.JSONDecodeError:
        print(f"Warning: Error parsing {QUOTA_FILE_PATH}. Using default models.")
        return ["gemini-2.5-flash", "gemini-2.0-flash"]


def load_available_prompts():
    """Load available prompts from prompts folder."""
    try:
        return [
            f.split(".")[0] for f in os.listdir(PROMPTS_FOLDER) if f.endswith(".md")
        ]
    except Exception as e:
        print(f"Warning: Error loading prompts: {e}")
        return ["technical_summary"]


# Validate configuration
if not TELEGRAM_BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
    exit(1)
