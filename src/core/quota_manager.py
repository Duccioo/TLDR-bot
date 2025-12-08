"""
Module for managing API quotas and models for Google Gemini, Groq, and OpenRouter.
"""

import json
import os
import time
import requests
from threading import RLock
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

from config import GROQ_API_KEY, OPENROUTER_API_KEY

request_timestamps = {}
QUOTA_FILE = os.path.join("data", "quota.json")
lock = RLock()


def initialize_quota_file():
    """
    Initializes the quota.json file with data from Gemini, Groq, and OpenRouter.
    """
    # Default data structure
    default_quota_data = {
        "gemini": {
             "gemini-2.5-flash": {
                "requests_per_minute": 10,
                "tokens_per_minute": 250000,
                "requests_per_day": 250,
                "usage_timestamps": [],
            },
            "gemini-2.0-flash": {
                "requests_per_minute": 15,
                "tokens_per_minute": 1000000,
                "requests_per_day": 200,
                "usage_timestamps": [],
            },
        },
        "groq": {},
        "openrouter": {}
    }

    # Fetch models from APIs
    try:
        if GROQ_API_KEY:
            groq_models = fetch_groq_models()
            for model in groq_models:
                 # Default Groq Free Tier limits (approximate/conservative)
                default_quota_data["groq"][model] = {
                    "requests_per_minute": 30,
                    "requests_per_day": 14400, # Approx
                    "tokens_per_minute": 6000,
                    "usage_timestamps": []
                }
    except Exception as e:
        print(f"Error initializing Groq models: {e}")

    try:
        if OPENROUTER_API_KEY:
            openrouter_models = fetch_openrouter_models()
            for model in openrouter_models:
                default_quota_data["openrouter"][model] = {
                    "usage_timestamps": []
                }
    except Exception as e:
        print(f"Error initializing OpenRouter models: {e}")

    # Create directory if not exists
    os.makedirs(os.path.dirname(QUOTA_FILE), exist_ok=True)

    # Save data
    with open(QUOTA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_quota_data, f, indent=4)

    print(f"✅ File {QUOTA_FILE} initialized successfully!")
    return default_quota_data


def get_quota_data():
    """Reads quota data from JSON file."""
    with lock:
        try:
            with open(QUOTA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  File {QUOTA_FILE} not found. Initializing...")
            return initialize_quota_file()
        except json.JSONDecodeError:
            print(f"⚠️  Error parsing {QUOTA_FILE}. Re-initializing...")
            return initialize_quota_file()


def save_quota_data(data):
    """Saves quota data to JSON file."""
    with lock:
        os.makedirs(os.path.dirname(QUOTA_FILE), exist_ok=True)
        with open(QUOTA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


def fetch_groq_models() -> List[str]:
    """Fetches available models from Groq API."""
    if not GROQ_API_KEY:
        return []

    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return [model["id"] for model in data.get("data", [])]
    except Exception as e:
        print(f"Error fetching Groq models: {e}")
        return []


def fetch_openrouter_models() -> List[str]:
    """Fetches available models from OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return []

    url = "https://openrouter.ai/api/v1/models"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Sort by pricing (low to high) or popularity could be better, but just taking top 20 for now to avoid huge lists
        models = [model["id"] for model in data.get("data", [])]
        # Filter mostly free or popular ones could be good, but let's return all and let UI handle or limit
        return models[:30] # Limit to top 30 to avoid blowing up the UI
    except Exception as e:
        print(f"Error fetching OpenRouter models: {e}")
        return []


def get_openrouter_quota_info() -> Dict[str, Any]:
    """Fetches quota/credit info from OpenRouter."""
    if not OPENROUTER_API_KEY:
        return {}

    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {})
        return {}
    except Exception as e:
        print(f"Error checking OpenRouter quota: {e}")
        return {}


def sync_models():
    """Updates the quota file with currently available models."""
    data = get_quota_data()
    updated = False

    if GROQ_API_KEY:
        current_groq = data.get("groq", {})
        fetched_groq = fetch_groq_models()
        for model in fetched_groq:
            if model not in current_groq:
                current_groq[model] = {
                    "requests_per_minute": 30, # Default conservative
                    "requests_per_day": 14400,
                    "tokens_per_minute": 6000,
                    "usage_timestamps": []
                }
                updated = True
        data["groq"] = current_groq

    if OPENROUTER_API_KEY:
        current_or = data.get("openrouter", {})
        fetched_or = fetch_openrouter_models()
        for model in fetched_or:
            if model not in current_or:
                current_or[model] = { "usage_timestamps": [] }
                updated = True
        data["openrouter"] = current_or

    if updated:
        save_quota_data(data)


def update_model_usage(model_name: str, token_count: int, provider: str = "gemini"):
    """
    Updates usage for a model.
    """
    with lock:
        data = get_quota_data()

        # Handle provider detection if not explicit (legacy support)
        if provider == "gemini" and model_name not in data.get("gemini", {}):
            # Try to find model in other providers
            if model_name in data.get("groq", {}):
                provider = "groq"
            elif model_name in data.get("openrouter", {}):
                provider = "openrouter"

        if provider in data and model_name in data[provider]:
            if "usage_timestamps" not in data[provider][model_name]:
                data[provider][model_name]["usage_timestamps"] = []

            usage_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tokens": token_count,
            }
            data[provider][model_name]["usage_timestamps"].append(usage_record)

            # Keep only last 24h of history to prevent file bloat
            now = datetime.now(timezone.utc)
            data[provider][model_name]["usage_timestamps"] = [
                r for r in data[provider][model_name]["usage_timestamps"]
                if now - datetime.fromisoformat(r["timestamp"]) < timedelta(days=1)
            ]

            save_quota_data(data)


def get_quota_summary():
    """
    Returns a text summary of usage quotas.
    """
    with lock:
        data = get_quota_data()
        summary = "<b>📊 API Quota Summary</b>\n\n"
        now = datetime.now(timezone.utc)

        # Gemini
        if "gemini" in data:
            summary += "<b>🔹 Google Gemini (Free Tier)</b>\n"
            for model, details in data["gemini"].items():
                rpm_limit = details.get("requests_per_minute", 0)
                timestamps = details.get("usage_timestamps", [])

                # Filter last minute
                recent_requests = [
                    r for r in timestamps
                    if now - datetime.fromisoformat(r["timestamp"]) <= timedelta(minutes=1)
                ]
                rpm_usage = len(recent_requests)

                summary += f"• <code>{model}</code>: {rpm_usage}/{rpm_limit} RPM\n"
            summary += "\n"

        # Groq
        if "groq" in data and GROQ_API_KEY:
            summary += "<b>🔹 Groq</b>\n"
            # Show aggregate or per model? Groq limits are usually global or per-model group
            # Just showing active models usage for brevity
            active_models = [m for m, d in data["groq"].items() if d.get("usage_timestamps")]
            if not active_models:
                 summary += "<i>No recent usage.</i>\n"
            for model in active_models:
                details = data["groq"][model]
                rpm_limit = details.get("requests_per_minute", 30)
                timestamps = details.get("usage_timestamps", [])
                recent_requests = [
                    r for r in timestamps
                    if now - datetime.fromisoformat(r["timestamp"]) <= timedelta(minutes=1)
                ]
                summary += f"• <code>{model}</code>: {len(recent_requests)}/{rpm_limit} RPM\n"
            summary += "\n"

        # OpenRouter
        if "openrouter" in data and OPENROUTER_API_KEY:
            summary += "<b>🔹 OpenRouter</b>\n"
            or_info = get_openrouter_quota_info()
            if or_info:
                limit = or_info.get("limit")
                usage = or_info.get("usage", 0)

                limit_str = f"${limit:.2f}" if limit else "Unlimited"
                usage_str = f"${usage:.4f}"

                summary += f"• Credit Used: {usage_str} / {limit_str}\n"
            else:
                summary += "<i>Could not fetch credit info.</i>\n"

        return summary


def wait_for_rate_limit(model_name: str, provider: str = "gemini"):
    """
    Checks rate limits and waits if necessary.
    """
    data = get_quota_data()

    # Auto-detect provider if default
    if provider == "gemini" and model_name not in data.get("gemini", {}):
         if model_name in data.get("groq", {}):
             provider = "groq"
         elif model_name in data.get("openrouter", {}):
             provider = "openrouter"

    if provider not in data or model_name not in data[provider]:
        return

    # Check RPM
    limit = data[provider][model_name].get("requests_per_minute", 0)
    if limit <= 0:
        return

    with lock:
        now = time.time()
        key = f"{provider}:{model_name}"

        if key not in request_timestamps:
            request_timestamps[key] = []

        # Clean old timestamps
        request_timestamps[key] = [
            t for t in request_timestamps[key] if now - t < 60
        ]

        if len(request_timestamps[key]) >= limit:
            time_to_wait = 60 - (now - request_timestamps[key][0]) + 1 # +1 buffer
            print(f"--- Rate limit reached for {model_name} ({provider}). Waiting {time_to_wait:.2f}s ---")
            time.sleep(time_to_wait)

        request_timestamps[key].append(time.time())
