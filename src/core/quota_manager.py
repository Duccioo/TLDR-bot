"""
Modulo per la gestione delle quote API di Google Gemini.
"""

import json
from threading import Lock

QUOTA_FILE = "src/data/quota.json"
lock = Lock()

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
            json.dump(data, f, indent=2)

def increment_request_count(model_name: str):
    """Incrementa il contatore delle richieste per un modello."""
    data = get_quota_data()
    if model_name not in data:
        data[model_name] = {"requests": 0}
    data[model_name]["requests"] += 1
    save_quota_data(data)

def get_quota_summary():
    """Restituisce un riepilogo testuale delle quote utilizzate."""
    data = get_quota_data()
    if not data:
        return "Nessun dato sulle quote disponibile."

    summary = "<b>Riepilogo Quote API Gemini:</b>\\n\\n"
    for model, stats in data.items():
        summary += f"<b>Modello:</b> {model}\\n"
        summary += f"  - Richieste effettuate: {stats['requests']}\\n"

    return summary
