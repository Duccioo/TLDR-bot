"""
Modulo per la gestione del rate limiting delle API di Google Gemini.
"""

import time
import json
from threading import Lock

# Struttura per memorizzare i timestamp delle richieste
request_timestamps = {}
lock = Lock()

# Carica i limiti di richieste da un file di configurazione
def load_rate_limits():
    # In un'implementazione reale, questo verrebbe da un file di configurazione
    return {
        "gemini-1.5-flash": {"rpm": 15},
        "gemini-1.5-pro": {"rpm": 2},
        "gemini-pro": {"rpm": 2},
    }

RATE_LIMITS = load_rate_limits()

def wait_for_rate_limit(model_name: str):
    """
    Controlla se una nuova richiesta rispetta il rate limit.
    Se il limite è stato raggiunto, attende il tempo necessario.
    """
    with lock:
        if model_name not in RATE_LIMITS:
            return  # Nessun limite specificato per questo modello

        limit = RATE_LIMITS[model_name]["rpm"]
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
            print(f"--- Rate limit raggiunto per {model_name}. Attesa di {time_to_wait:.2f} secondi. ---")
            time.sleep(time_to_wait)

        # Aggiungi il timestamp della nuova richiesta
        request_timestamps[model_name].append(time.time())
