import time
from collections import deque
from datetime import datetime, timedelta
import requests


class GeminiRateLimitTracker:
    def __init__(self):
        # Limiti Free Tier
        self.RPM_LIMIT = 15  # Richieste per minuto
        self.RPD_LIMIT = 1500  # Richieste per giorno
        self.TPD_LIMIT = 1_000_000  # Token per giorno

        # Tracking
        self.requests_last_minute = deque()
        self.requests_today = []
        self.tokens_today = 0
        self.current_day = datetime.now().date()

    def _reset_daily_if_needed(self):
        """Reset contatori se è un nuovo giorno"""
        today = datetime.now().date()
        if today != self.current_day:
            self.requests_today = []
            self.tokens_today = 0
            self.current_day = today
            print(f"📅 Nuovo giorno! Contatori resettati.")

    def _clean_old_requests(self):
        """Rimuovi richieste più vecchie di 1 minuto"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        while (
            self.requests_last_minute and self.requests_last_minute[0] < one_minute_ago
        ):
            self.requests_last_minute.popleft()

    def can_make_request(self):
        """Controlla se possiamo fare una richiesta"""
        self._reset_daily_if_needed()
        self._clean_old_requests()

        # Controlla RPM
        if len(self.requests_last_minute) >= self.RPM_LIMIT:
            return False, "RPM limit reached"

        # Controlla RPD
        if len(self.requests_today) >= self.RPD_LIMIT:
            return False, "RPD limit reached"

        # Controlla TPD (approssimativo, non sappiamo i token prima della richiesta)
        if self.tokens_today >= self.TPD_LIMIT * 0.95:  # 95% di sicurezza
            return False, "TPD limit approaching"

        return True, "OK"

    def add_request(self, tokens_used):
        """Registra una richiesta completata"""
        now = datetime.now()
        self.requests_last_minute.append(now)
        self.requests_today.append(now)
        self.tokens_today += tokens_used

    def get_stats(self):
        """Ottieni statistiche correnti"""
        self._reset_daily_if_needed()
        self._clean_old_requests()

        return {
            "rpm": {
                "used": len(self.requests_last_minute),
                "limit": self.RPM_LIMIT,
                "remaining": self.RPM_LIMIT - len(self.requests_last_minute),
            },
            "rpd": {
                "used": len(self.requests_today),
                "limit": self.RPD_LIMIT,
                "remaining": self.RPD_LIMIT - len(self.requests_today),
            },
            "tpd": {
                "used": self.tokens_today,
                "limit": self.TPD_LIMIT,
                "remaining": self.TPD_LIMIT - self.tokens_today,
            },
        }

    def wait_time_needed(self):
        """Calcola quanto tempo aspettare"""
        if not self.requests_last_minute:
            return 0
        oldest = self.requests_last_minute[0]
        wait = 60 - (datetime.now() - oldest).total_seconds()
        return max(0, wait)


# === USO ===
API_KEY = "tua_chiave_api"
url = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
)

tracker = GeminiRateLimitTracker()


def call_gemini_safe(prompt):
    # Controlla se possiamo fare la richiesta
    can_request, reason = tracker.can_make_request()

    if not can_request:
        wait = tracker.wait_time_needed()
        print(f"⚠️ {reason}")
        if wait > 0:
            print(f"⏳ Attendo {wait:.1f} secondi...")
            time.sleep(wait + 1)

    # Fai la richiesta
    params = {"key": API_KEY}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, params=params, json=payload)

    if response.status_code == 200:
        data = response.json()

        # Estrai i token usati
        tokens_used = data.get("usageMetadata", {}).get("totalTokenCount", 0)

        # Registra la richiesta
        tracker.add_request(tokens_used)

        # Mostra statistiche
        stats = tracker.get_stats()
        print(f"\n📊 STATISTICHE:")
        print(
            f"   RPM: {stats['rpm']['used']}/{stats['rpm']['limit']} (rimangono {stats['rpm']['remaining']})"
        )
        print(
            f"   RPD: {stats['rpd']['used']}/{stats['rpd']['limit']} (rimangono {stats['rpd']['remaining']})"
        )
        print(
            f"   TPD: {stats['tpd']['used']:,}/{stats['tpd']['limit']:,} (rimangono {stats['tpd']['remaining']:,})"
        )
        print(f"   Token questa richiesta: {tokens_used}\n")

        return data

    elif response.status_code == 429:
        print(f"❌ Rate limit dal server: {response.json()}")
        return None

    else:
        print(f"❌ Errore {response.status_code}: {response.text}")
        return None


# === TEST ===
if __name__ == "__main__":
    # Prova alcune richieste
    for i in range(3):
        print(f"\n{'='*50}")
        print(f"Richiesta #{i+1}")
        print("=" * 50)

        result = call_gemini_safe(f"Di ciao {i+1}")

        if result:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"Risposta: {text}")

        time.sleep(1)  # Piccola pausa tra le richieste
