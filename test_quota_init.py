"""
Script di test per verificare l'inizializzazione del file quota.json
"""

import os
import json

# Rimuovi il file se esiste per testare l'inizializzazione
QUOTA_FILE = "src/data/quota.json"
if os.path.exists(QUOTA_FILE):
    print(f"🗑️  Rimozione file esistente: {QUOTA_FILE}")
    os.remove(QUOTA_FILE)

# Importa e testa la funzione
from src.core.quota_manager import get_quota_data

print("\n📋 Test inizializzazione quota.json...")
data = get_quota_data()

print("\n✅ Dati caricati con successo!")
print(f"📊 Numero di modelli: {len(data.get('gemini', {}))}")
print("\n🔹 Modelli disponibili:")
for model_name in data.get("gemini", {}).keys():
    print(f"  - {model_name}")

print(f"\n📁 File creato in: {os.path.abspath(QUOTA_FILE)}")

# Verifica che il file esista
if os.path.exists(QUOTA_FILE):
    print("✅ File quota.json creato correttamente!")
    with open(QUOTA_FILE, "r", encoding="utf-8") as f:
        file_data = json.load(f)
        print(f"📦 Dimensione file: {len(json.dumps(file_data))} bytes")
else:
    print("❌ Errore: file non creato!")
