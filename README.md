# TLDR-bot

Bot per estrarre, riassumere e pubblicare articoli web utilizzando Trafilatura e Google Gemini.

## 🚀 Caratteristiche

- **Estrazione contenuti**: Estrai testo, metadati e immagini da qualsiasi URL
- **Formati multipli**: Supporto per Markdown, HTML e testo semplice
- **Riassunti AI**: Genera riassunti intelligenti con Google Gemini
- **Pubblicazione Telegraph**: Pubblica automaticamente su Telegra.ph
- **Hashtag intelligenti**: Generazione automatica di hashtag rilevanti
- **🆕 Formattazione Avanzata**: Sistema intelligente che preserva abbreviazioni (Dr., Inc., MJ.) e numeri

## 📦 Installazione

1. Clona il repository:
```bash
git clone https://github.com/Duccioo/TLDR-bot.git
cd TLDR-bot
```

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura le variabili d'ambiente:
```bash
cp .env.example .env
```

4. Modifica il file `.env` e aggiungi la tua API key di Google Gemini:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

> 💡 Ottieni la tua chiave API gratuita da: https://makersuite.google.com/app/apikey

## 📚 Struttura del Progetto

```
TLDR-bot/
├── src/
│   ├── bot.py                # 🆕 Entry point del bot (modulare)
│   ├── config.py             # 🆕 Configurazione centralizzata
│   ├── decorators.py         # 🆕 Decoratori personalizzati
│   ├── keyboards.py          # 🆕 Definizione tastiere Telegram
│   ├── utils.py              # Funzioni di utilità
│   ├── handlers/             # 🆕 Gestori modulari del bot
│   │   ├── auth_handlers.py
│   │   ├── command_handlers.py
│   │   ├── conversation_handlers.py
│   │   ├── message_handlers.py
│   │   └── callback_handlers.py
│   ├── core/
│   │   ├── extractor.py      # Funzioni di estrazione contenuti
│   │   ├── summarizer.py     # Generazione riassunti con Gemini
│   │   ├── scraper.py        # Pubblicazione su Telegra.ph
│   │   ├── quota_manager.py  # Gestione quote API
│   │   └── rate_limiter.py   # Rate limiting
│   ├── prompts/              # Template dei prompt
│   └── data/
│       └── quota.json        # Dati sulle quote API
├── docs/                     # Documentazione dettagliata
├── STRUCTURE.md              # 🆕 Documentazione struttura modulare
├── MIGRATION.md              # 🆕 Guida alla migrazione
├── test_structure.py         # 🆕 Test della nuova struttura
├── .env.example              # Template variabili d'ambiente
├── requirements.txt          # Dipendenze Python
└── README.md                 # Questo file
```

> **🔥 Novità**: Il bot è stato ristrutturato in moduli per migliorare manutenibilità e scalabilità!  
> Vedi [STRUCTURE.md](STRUCTURE.md) per dettagli sulla nuova architettura e [MIGRATION.md](MIGRATION.md) per la guida alla migrazione.

## 🎯 Utilizzo

### Bot Telegram

#### Avvio del bot (Nuova Struttura Modulare) ✅
```bash
python src/bot.py
```

#### Avvio del bot (Vecchio Metodo - Ancora Funzionante)
```bash
python src/telegram_bot.py
```

Il bot Telegram offre:
- 📝 Selezione prompt personalizzati
- 🤖 Cambio modello AI
- 🌐 Ricerca web opzionale
- 🔗 Contesto URL
- 📊 Monitoraggio quota API

### Estrazione Contenuti

```python
from src.core.extractor import estrai_come_markdown, estrai_contenuto_da_url

# Estrai in formato Markdown
markdown = estrai_come_markdown("https://example.com/article")
print(markdown)

# Estrai contenuto strutturato
article = estrai_contenuto_da_url("https://example.com/article")
print(f"Titolo: {article.title}")
print(f"Autore: {article.author}")
print(f"Testo: {article.text}")
```

### Riassunti con AI

```python
from src.core.extractor import estrai_contenuto_da_url
from src.core.summarizer import summarize_article

# Estrai l'articolo
article = estrai_contenuto_da_url("https://example.com/article")

# Genera un riassunto
summary = summarize_article(
    article=article,
    summary_type="brief",  # o altro tipo di prompt
    model_name="gemini-1.5-flash"
)
print(summary)
```

### Pubblicazione su Telegraph

```python
from src.core.scraper import crea_articolo_telegraph

# Pubblica direttamente da un URL
telegraph_url = crea_articolo_telegraph(
    "https://example.com/article",
    author_name="Bot TLDR"
)
print(f"Articolo pubblicato: {telegraph_url}")
```

## 🔧 Configurazione

### Modelli Gemini Disponibili

- `gemini-1.5-flash` (default): Veloce ed economico
- `gemini-1.5-pro`: Più potente, per compiti complessi
- `gemini-pro`: Versione stabile precedente

### Personalizzazione Prompt

I prompt per i riassunti si trovano in `src/bot/prompts/`. Puoi creare i tuoi template usando variabili come:

- `{{title}}` - Titolo dell'articolo
- `{{text}}` - Testo completo
- `{{author}}` - Autore
- `{{date}}` - Data di pubblicazione
- `{{url}}` - URL originale
- `{{sitename}}` - Nome del sito

## 📖 Documentazione Completa

Per la documentazione dettagliata di tutte le funzioni, consulta la cartella [docs](docs/).

## 🛠️ Requisiti

- Python 3.8+
- Connessione internet
- API Key Google Gemini (gratuita)

## 📝 Licenza

MIT License - vedi il file [LICENSE](LICENSE) per i dettagli.

## 🤝 Contributi

I contributi sono benvenuti! Sentiti libero di aprire issue o pull request.
