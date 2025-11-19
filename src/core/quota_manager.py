"""
Modulo per la gestione delle quote API di Google Gemini.
"""

import json
import os
import time
from threading import RLock
from datetime import datetime, timedelta, timezone

request_timestamps = {}
QUOTA_FILE = os.path.join("data", "quota.json")
lock = RLock()  # Changed from Lock to RLock to allow re-entrant locking


def initialize_quota_file():
    """
    Inizializza il file quota.json con i dati dei modelli text-out del free tier di Google Gemini.
    Dati presi da: https://ai.google.dev/gemini-api/docs/rate-limits#free-tier
    """
    # Dati aggiornati al 19 ottobre 2025 per il free tier (text-out models)
    default_quota_data = {
        "gemini": {
            "gemini-2.5-pro": {
                "requests_per_minute": 2,
                "tokens_per_minute": 125000,
                "requests_per_day": 50,
                "usage_timestamps": [],
            },
            "gemini-2.5-flash": {
                "requests_per_minute": 10,
                "tokens_per_minute": 250000,
                "requests_per_day": 250,
                "usage_timestamps": [],
            },
            "gemini-2.5-flash-preview": {
                "requests_per_minute": 10,
                "tokens_per_minute": 250000,
                "requests_per_day": 250,
                "usage_timestamps": [],
            },
            "gemini-2.5-flash-lite": {
                "requests_per_minute": 15,
                "tokens_per_minute": 250000,
                "requests_per_day": 1000,
                "usage_timestamps": [],
            },
            "gemini-2.5-flash-lite-preview": {
                "requests_per_minute": 15,
                "tokens_per_minute": 250000,
                "requests_per_day": 1000,
                "usage_timestamps": [],
            },
            "gemini-2.0-flash": {
                "requests_per_minute": 15,
                "tokens_per_minute": 1000000,
                "requests_per_day": 200,
                "usage_timestamps": [],
            },
            "gemini-2.0-flash-lite": {
                "requests_per_minute": 30,
                "tokens_per_minute": 1000000,
                "requests_per_day": 200,
                "usage_timestamps": [],
            },
        }
    }
    # Crea la directory se non esiste
    os.makedirs(os.path.dirname(QUOTA_FILE), exist_ok=True)

    # Salva i dati nel file
    with open(QUOTA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_quota_data, f, indent=4)

    print(f"✅ File {QUOTA_FILE} inizializzato con successo!")
    return default_quota_data


def get_quota_data():
    """Legge i dati sulle quote dal file JSON."""
    with lock:
        try:
            with open(QUOTA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # Se il file non esiste, lo inizializza
            print(f"⚠️  File {QUOTA_FILE} non trovato. Inizializzazione in corso...")
            return initialize_quota_file()
        except json.JSONDecodeError:
            print(f"⚠️  Errore nel parsing di {QUOTA_FILE}. Reinizializzazione...")
            return initialize_quota_file()


def save_quota_data(data):
    """Salva i dati sulle quote nel file JSON."""
    with lock:
        # Crea la directory se non esiste
        os.makedirs(os.path.dirname(QUOTA_FILE), exist_ok=True)
        with open(QUOTA_FILE, "w", encoding="utf-8") as f:
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
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
        now = datetime.now(timezone.utc)
        for model, details in data["gemini"].items():
            rpm_limit = details.get("requests_per_minute", 0)
            rpd_limit = details.get("requests_per_day", 0)
            tpm_limit = details.get("tokens_per_minute", 0)
            timestamps = details.get("usage_timestamps", [])

            # Filtra le richieste dell'ultimo minuto
            recent_requests = []
            for r in timestamps:
                ts = datetime.fromisoformat(r["timestamp"])
                # Se il timestamp è naive, aggiungilo il timezone UTC
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if now - ts <= timedelta(minutes=1):
                    recent_requests.append(r)

            rpm_usage = len(recent_requests)
            tpm_usage = sum(r["tokens"] for r in recent_requests)
            rpm_percentage = (rpm_usage / rpm_limit * 100) if rpm_limit > 0 else 0
            tpm_percentage = (tpm_usage / tpm_limit * 100) if tpm_limit > 0 else 0

            # Filtra le richieste di oggi
            today_requests = []
            for r in timestamps:
                ts = datetime.fromisoformat(r["timestamp"])
                # Se il timestamp è naive, aggiungilo il timezone UTC
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if now.date() == ts.date():
                    today_requests.append(r)

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


def wait_for_rate_limit(model_name: str):
    """
    Controlla se una nuova richiesta rispetta il rate limit.
    Se il limite è stato raggiunto, attende il tempo necessario.
    """
    rate_limits = get_quota_data()["gemini"]

    with lock:
        if model_name not in rate_limits:
            return  # Nessun limite specificato per questo modello

        limit = rate_limits[model_name]["requests_per_minute"]
        now = time.time()

        if model_name not in request_timestamps:
            request_timestamps[model_name] = []

        # Rimuovi i timestamp più vecchi di un minuto
        request_timestamps[model_name] = [
            t for t in request_timestamps[model_name] if now - t < 60
        ]

        if len(request_timestamps[model_name]) >= limit:
            # Calcola il tempo di attesa
            time_to_wait = 60 - (now - request_timestamps[model_name][0])
            print(
                f"--- Rate limit raggiunto per {model_name}. Attesa di {time_to_wait:.2f} secondi. ---"
            )
            time.sleep(time_to_wait)

        # Aggiungi il timestamp della nuova richiesta
        request_timestamps[model_name].append(time.time())
