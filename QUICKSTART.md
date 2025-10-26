# 🚀 Guida Rapida - TLDR Bot

Inizia a usare TLDR Bot in 5 minuti!

## ⚡ Setup Veloce

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura l'API Key

Copia il file di esempio:
```bash
cp .env.example .env
```

Modifica `.env` e aggiungi la tua chiave API di Google Gemini:
```bash
GEMINI_API_KEY=your_api_key_here
```

> 💡 Ottieni una chiave gratuita da: https://makersuite.google.com/app/apikey

### 3. Prova il bot!

```bash
python test_bot.py
```

## 📝 Esempi Veloci

### Estrai un articolo

```python
from src.extractor import estrai_contenuto_da_url

article = estrai_contenuto_da_url("https://example.com/article")
print(article.title)
print(article.text)
```

### Genera un riassunto con AI

```python
from src.summarizer import summarize_article

summary = summarize_article(article, summary_type="brief")
print(summary)
```

### Pubblica su Telegraph

```python
from src.scraper import crea_articolo_telegraph

url = crea_articolo_telegraph("https://example.com/article")
print(f"Pubblicato: {url}")
```

## 🎯 Workflow Completo

```python
from src.extractor import estrai_contenuto_da_url
from src.summarizer import summarize_article
from src.scraper import crea_articolo_telegraph

# 1. Estrai l'articolo
url_originale = "https://example.com/article"
article = estrai_contenuto_da_url(url_originale)

# 2. Genera un riassunto
summary = summarize_article(article, summary_type="brief")
print("Riassunto:", summary)

# 3. Pubblica su Telegraph
telegraph_url = crea_articolo_telegraph(url_originale)
print("Pubblicato su:", telegraph_url)
```

## 📚 Documentazione

- **Estrazione**: Vedi [src/README.md](src/README.md)
- **Riassunti AI**: Vedi [docs/SUMMARIZER.md](docs/SUMMARIZER.md)
- **README completo**: Vedi [README.md](README.md)

## ❓ Hai problemi?

### L'API Key non funziona
- Verifica di aver copiato correttamente la chiave nel file `.env`
- Assicurati che il file `.env` sia nella root del progetto
- Controlla che la chiave sia attiva su Google AI Studio

### Errore "Module not found"
```bash
pip install -r requirements.txt
```

### Altri problemi
Apri una issue su GitHub o consulta la documentazione completa.

## 🎓 Prossimi Passi

1. Esplora i diversi formati di estrazione (Markdown, HTML)
2. Crea i tuoi prompt personalizzati in `src/prompts/`
3. Sperimenta con diversi modelli Gemini
4. Integra il bot nel tuo workflow

Buon divertimento! 🎉
