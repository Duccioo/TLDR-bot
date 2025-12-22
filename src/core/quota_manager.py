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
            # Gemini Flash Models
            "gemini-2.5-flash": {
                "requests_per_minute": 5,
                "tokens_per_minute": 250000,
                "requests_per_day": 20,
                "usage_timestamps": [],
            },
            "gemini-2.5-flash-lite": {
                "requests_per_minute": 10,
                "tokens_per_minute": 250000,
                "requests_per_day": 20,
                "usage_timestamps": [],
            },
            "gemini-3-flash-preview": {
                "requests_per_minute": 5,
                "tokens_per_minute": 250000,
                "requests_per_day": 20,
                "usage_timestamps": [],
            },
            # Gemma 3 Models
            "gemma-3-12b": {
                "requests_per_minute": 30,
                "tokens_per_minute": 15000,
                "requests_per_day": 14400,
                "usage_timestamps": [],
            },
            "gemma-3-1b": {
                "requests_per_minute": 30,
                "tokens_per_minute": 15000,
                "requests_per_day": 14400,
                "usage_timestamps": [],
            },
            "gemma-3-27b": {
                "requests_per_minute": 30,
                "tokens_per_minute": 15000,
                "requests_per_day": 14400,
                "usage_timestamps": [],
            },
            "gemma-3-2b": {
                "requests_per_minute": 30,
                "tokens_per_minute": 15000,
                "requests_per_day": 14400,
                "usage_timestamps": [],
            },
            "gemma-3-4b": {
                "requests_per_minute": 30,
                "tokens_per_minute": 15000,
                "requests_per_day": 14400,
                "usage_timestamps": [],
            },
        },
        "groq": {},
        "openrouter": {},
    }

    # Fetch models from APIs
    try:
        if GROQ_API_KEY:
            groq_models = fetch_groq_models()
            for model in groq_models:
                # Default Groq Free Tier limits (approximate/conservative)
                default_quota_data["groq"][model] = {
                    "requests_per_minute": 30,
                    "requests_per_day": 14400,  # Approx
                    "tokens_per_minute": 6000,
                    "usage_timestamps": [],
                }
    except Exception as e:
        print(f"Error initializing Groq models: {e}")

    try:
        if OPENROUTER_API_KEY:
            openrouter_models = fetch_openrouter_models()
            for model in openrouter_models:
                default_quota_data["openrouter"][model] = {"usage_timestamps": []}
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
        "Content-Type": "application/json",
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
    """Fetches available :free models from OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return []

    url = "https://openrouter.ai/api/v1/models"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Filter only :free models as per user requirement
        models = [
            model["id"]
            for model in data.get("data", [])
            if model["id"].endswith(":free")
        ]
        return models
    except Exception as e:
        print(f"Error fetching OpenRouter models: {e}")
        return []


def get_openrouter_quota_info() -> Dict[str, Any]:
    """Fetches quota/credit info from OpenRouter."""
    if not OPENROUTER_API_KEY:
        return {}

    url = "https://openrouter.ai/api/v1/key"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {})
        return {}
    except Exception as e:
        print(f"Error checking OpenRouter quota: {e}")
        return {}


def update_groq_rate_limits(model_name: str, headers: dict):
    """
    Updates Groq rate limits from response headers.
    Headers expected:
    - x-ratelimit-limit-requests / x-ratelimit-remaining-requests
    - x-ratelimit-limit-tokens / x-ratelimit-remaining-tokens
    - x-ratelimit-reset-requests / x-ratelimit-reset-tokens
    """
    with lock:
        data = get_quota_data()
        if "groq" not in data or model_name not in data["groq"]:
            return

        model_data = data["groq"][model_name]

        # Parse headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in headers.items()}

        if "x-ratelimit-limit-requests" in headers_lower:
            try:
                model_data["requests_per_minute"] = int(headers_lower["x-ratelimit-limit-requests"])
            except ValueError:
                pass
        if "x-ratelimit-remaining-requests" in headers_lower:
            try:
                model_data["remaining_requests"] = int(headers_lower["x-ratelimit-remaining-requests"])
            except ValueError:
                pass
        if "x-ratelimit-limit-tokens" in headers_lower:
            try:
                model_data["tokens_per_minute"] = int(headers_lower["x-ratelimit-limit-tokens"])
            except ValueError:
                pass
        if "x-ratelimit-remaining-tokens" in headers_lower:
            try:
                model_data["remaining_tokens"] = int(headers_lower["x-ratelimit-remaining-tokens"])
            except ValueError:
                pass
        if "x-ratelimit-reset-requests" in headers_lower:
            model_data["reset_requests"] = headers_lower["x-ratelimit-reset-requests"]
        if "x-ratelimit-reset-tokens" in headers_lower:
            model_data["reset_tokens"] = headers_lower["x-ratelimit-reset-tokens"]

        save_quota_data(data)


def update_openrouter_limits():
    """Fetches and stores OpenRouter limits in quota data."""
    info = get_openrouter_quota_info()
    if not info:
        return

    with lock:
        data = get_quota_data()
        data["openrouter_limits"] = {
            "limit": info.get("limit"),
            "limit_remaining": info.get("limit_remaining"),
            "usage": info.get("usage", 0),
            "usage_daily": info.get("usage_daily", 0),
            "is_free_tier": info.get("is_free_tier", True),
        }
        save_quota_data(data)


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
                    "requests_per_minute": 30,  # Default conservative
                    "requests_per_day": 14400,
                    "tokens_per_minute": 6000,
                    "usage_timestamps": [],
                }
                updated = True
        data["groq"] = current_groq

    if OPENROUTER_API_KEY:
        current_or = data.get("openrouter", {})
        fetched_or = fetch_openrouter_models()
        for model in fetched_or:
            if model not in current_or:
                current_or[model] = {"usage_timestamps": []}
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
                r
                for r in data[provider][model_name]["usage_timestamps"]
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
                    r
                    for r in timestamps
                    if now - datetime.fromisoformat(r["timestamp"])
                    <= timedelta(minutes=1)
                ]
                rpm_usage = len(recent_requests)

                summary += f"• <code>{model}</code>: {rpm_usage}/{rpm_limit} RPM\n"
            summary += "\n"

        # Groq
        if "groq" in data and GROQ_API_KEY:
            summary += "<b>🔹 Groq</b>\n"
            # Show models that have rate limit data from headers
            active_models = [
                m for m, d in data["groq"].items()
                if d.get("remaining_requests") is not None or d.get("usage_timestamps")
            ]
            if not active_models:
                summary += "<i>Nessun utilizzo recente.</i>\n"
            for model in active_models:
                details = data["groq"][model]
                rpm_limit = details.get("requests_per_minute", 30)
                rpm_remaining = details.get("remaining_requests", "N/A")
                tpm_limit = details.get("tokens_per_minute", "N/A")
                tpm_remaining = details.get("remaining_tokens", "N/A")

                summary += f"• <code>{model}</code>\n"
                summary += f"  Requests: {rpm_remaining}/{rpm_limit} RPM\n"
                if tpm_limit != "N/A":
                    summary += f"  Tokens: {tpm_remaining}/{tpm_limit} TPM\n"
            summary += "\n"

        # OpenRouter
        if "openrouter" in data and OPENROUTER_API_KEY:
            summary += "<b>🔹 OpenRouter</b>\n"
            # First check stored limits, then fetch if not available
            or_info = data.get("openrouter_limits", {})
            if not or_info:
                or_info = get_openrouter_quota_info()
            if or_info:
                limit = or_info.get("limit")
                limit_remaining = or_info.get("limit_remaining")
                usage = or_info.get("usage", 0)
                usage_daily = or_info.get("usage_daily", 0)

                limit_str = f"${limit:.2f}" if limit else "Unlimited"
                usage_str = f"${usage:.4f}" if usage else "$0.00"

                summary += f"• Crediti usati: {usage_str} / {limit_str}\n"
                if limit_remaining is not None:
                    summary += f"• Rimanenti: ${limit_remaining:.4f}\n"
                if usage_daily:
                    summary += f"• Uso oggi: ${usage_daily:.4f}\n"
            else:
                summary += "<i>Impossibile recuperare info crediti.</i>\n"

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
        request_timestamps[key] = [t for t in request_timestamps[key] if now - t < 60]

        if len(request_timestamps[key]) >= limit:
            time_to_wait = 60 - (now - request_timestamps[key][0]) + 1  # +1 buffer
            print(
                f"--- Rate limit reached for {model_name} ({provider}). Waiting {time_to_wait:.2f}s ---"
            )
            time.sleep(time_to_wait)

        request_timestamps[key].append(time.time())
