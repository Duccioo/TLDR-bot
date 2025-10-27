"""
Modulo per la gestione delle quote API di Google Gemini.
"""

import json
from threading import RLock
from datetime import datetime, timedelta

QUOTA_FILE = "src/data/quota.json"
lock = RLock()  # Changed from Lock to RLock to allow re-entrant locking


def get_quota_data():
    """Legge i dati sulle quote dal file JSON."""
    with lock:
        try:
            with open(QUOTA_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}


def save_quota_data(data):
    """Salva i dati sulle quote nel file JSON."""
    with lock:
        with open(QUOTA_FILE, "w") as f:
            json.dump(data, f, indent=4)


def update_model_usage(model_name: str, token_count: int):
    """
    Aggiorna l'utilizzo di un modello, registrando timestamp e conteggio token.
    """
    with lock:
        data = get_quota_data()
        if "gemini" in data and model_name in data["gemini"]:
            if "usage_timestamps" not in data["gemini"][model_name]:
                data["gemini"][model_name]["usage_timestamps"] = []

            # Aggiunge un dizionario con timestamp e token
            usage_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "tokens": token_count,
            }
            data["gemini"][model_name]["usage_timestamps"].append(usage_record)
            save_quota_data(data)


def get_quota_summary():
    """
    Restituisce un riepilogo testuale delle quote di utilizzo, includendo RPM, RPD e TPM.
    """
    with lock:
        data = get_quota_data()
        if not data or "gemini" not in data:
            return "Nessun dato di quota disponibile."

        summary = "<b>Riepilogo Quote API Gemini (Free Tier):</b>\n\n"
        now = datetime.utcnow()

        for model, details in data["gemini"].items():
            rpm_limit = details.get("requests_per_minute", 0)
            rpd_limit = details.get("requests_per_day", 0)
            tpm_limit = details.get("tokens_per_minute", 0)
            timestamps = details.get("usage_timestamps", [])

            # Filtra le richieste dell'ultimo minuto
            recent_requests = [
                r
                for r in timestamps
                if now - datetime.fromisoformat(r["timestamp"]) <= timedelta(minutes=1)
            ]
            rpm_usage = len(recent_requests)
            tpm_usage = sum(r["tokens"] for r in recent_requests)
            rpm_percentage = (rpm_usage / rpm_limit * 100) if rpm_limit > 0 else 0
            tpm_percentage = (tpm_usage / tpm_limit * 100) if tpm_limit > 0 else 0

            # Filtra le richieste di oggi
            today_requests = [
                r
                for r in timestamps
                if now.date() == datetime.fromisoformat(r["timestamp"]).date()
            ]
            rpd_usage = len(today_requests)
            rpd_percentage = (rpd_usage / rpd_limit * 100) if rpd_limit > 0 else 0

            summary += f"<b>Modello:</b> <code>{model}</code>\n"
            summary += (
                f"  - <b>RPM:</b> {rpm_usage}/{rpm_limit} ({rpm_percentage:.2f}%)\n"
            )
            summary += (
                f"  - <b>TPM:</b> {tpm_usage}/{tpm_limit} ({tpm_percentage:.2f}%)\n"
            )
            summary += (
                f"  - <b>RPD:</b> {rpd_usage}/{rpd_limit} ({rpd_percentage:.2f}%)\n\n"
            )

        return summary
