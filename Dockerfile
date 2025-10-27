# Usa un'immagine Python ufficiale leggera e multi-architettura
FROM python:3.11-slim-bookworm

# Imposta la directory di lavoro nel container
WORKDIR /app

# Copia il file delle dipendenze e installale
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice dell'applicazione
COPY src/ ./src/

# Imposta il comando per avviare il bot
CMD ["python", "src/telegram_bot.py"]
