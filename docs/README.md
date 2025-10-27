# TLDR-bot - Documentazione

Questa documentazione descrive i moduli principali del progetto TLDR-bot.

## Struttura del Progetto

```
src/
├── core/
│   ├── extractor.py      # Funzioni di estrazione contenuti
│   ├── summarizer.py     # Generazione riassunti con Gemini
│   └── scraper.py        # Pubblicazione su Telegra.ph
├── bot/
│   ├── telegram_bot.py   # Logica del bot Telegram
│   └── prompts/          # Template dei prompt
└── data/
    └── quota.json        # Dati sulle quote API
```

## Modulo `core/extractor.py`

Il modulo `extractor` fornisce diverse funzioni per estrarre contenuti da URL.

### Funzioni Principali

#### `estrai_contenuto_da_url(url, timeout=15, include_images=True, include_links=True)`

Estrae il contenuto completo da un URL e restituisce un oggetto `ArticleContent`.

```python
from src.core.extractor import estrai_contenuto_da_url

article = estrai_contenuto_da_url("https://example.com/article")
if article:
    print(f"Titolo: {article.title}")
    print(f"Autore: {article.author}")
    print(f"Data: {article.date}")
    print(f"Testo: {article.text}")
```

**Campi disponibili in `ArticleContent`:**
- `title`: Titolo dell'articolo
- `text`: Testo principale in formato testo semplice
- `author`: Autore dell'articolo (se disponibile)
- `date`: Data di pubblicazione (se disponibile)
- `url`: URL originale
- `description`: Descrizione/sommario (se disponibile)
- `sitename`: Nome del sito web
- `categories`: Categorie dell'articolo
- `tags`: Tag associati

#### `estrai_come_markdown(url, timeout=15, include_metadata=True)`

Estrae il contenuto e lo formatta in Markdown con metadati opzionali.

```python
from src.core.extractor import estrai_come_markdown

markdown = estrai_come_markdown("https://example.com/article")
if markdown:
    with open("article.md", "w", encoding="utf-8") as f:
        f.write(markdown)
```

**Output esempio:**
```markdown
---
# Titolo dell'articolo

**Autore:** Nome Autore
**Data:** 2025-10-25
**Fonte:** Example.com

_Breve descrizione dell'articolo_

**URL originale:** https://example.com/article
---

## Contenuto

Il testo dell'articolo in formato Markdown...
```

#### `estrai_come_html(url, timeout=15, pulisci_html=True)`

Estrae il contenuto in formato HTML pulito e validato.

```python
from src.core.extractor import estrai_come_html

html = estrai_come_html("https://example.com/article")
if html:
    print(html)
```

#### `estrai_metadati(url, timeout=15)`

Estrae solo i metadati senza il contenuto completo (più veloce).

```python
from src.core.extractor import estrai_metadati

metadata = estrai_metadati("https://example.com/article")
if metadata:
    print(f"Titolo: {metadata['title']}")
    print(f"Autore: {metadata['author']}")
    print(f"Data: {metadata['date']}")
```

## Modulo `core/scraper.py`

Il modulo `scraper` utilizza le funzioni di `extractor` per pubblicare contenuti su Telegra.ph.

### Funzione Principale

#### `crea_articolo_telegraph(url_articolo, author_name=None)`

Estrae il contenuto da un URL e lo pubblica su Telegra.ph.

```python
from src.core.scraper import crea_articolo_telegraph

url_telegraph = crea_articolo_telegraph(
    "https://example.com/article",
    author_name="Il mio nome"  # Opzionale
)

if url_telegraph:
    print(f"Articolo pubblicato: {url_telegraph}")
```

**Parametri:**
- `url_articolo`: URL dell'articolo da estrarre
- `author_name`: Nome dell'autore (opzionale, altrimenti usa quello estratto dall'articolo)

**Restituisce:**
- L'URL della pagina Telegra.ph creata, o `None` in caso di errore

## Esempi d'Uso

### Esempio 1: Estrazione semplice in Markdown

```python
from src.core.extractor import estrai_come_markdown

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]

for url in urls:
    markdown = estrai_come_markdown(url)
    if markdown:
        filename = url.split("/")[-1] + ".md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✓ Salvato: {filename}")
```

### Esempio 2: Estrazione e analisi metadati

```python
from src.core.extractor import estrai_metadati

url = "https://example.com/article"
metadata = estrai_metadati(url)

if metadata:
    print("Informazioni articolo:")
    print(f"  Titolo: {metadata['title']}")
    print(f"  Autore: {metadata['author']}")
    print(f"  Data: {metadata['date']}")
    print(f"  Sito: {metadata['sitename']}")
    if metadata['tags']:
        print(f"  Tags: {', '.join(metadata['tags'])}")
```

### Esempio 3: Pubblicazione batch su Telegra.ph

```python
from src.core.scraper import crea_articolo_telegraph

urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]

risultati = []
for url in urls:
    print(f"\nElaborazione: {url}")
    telegraph_url = crea_articolo_telegraph(url, author_name="Bot Scraper")
    
    if telegraph_url:
        risultati.append({"originale": url, "telegraph": telegraph_url})
        print(f"✓ Pubblicato: {telegraph_url}")
    else:
        print(f"✗ Errore con {url}")

print(f"\n\nTotale pubblicazioni riuscite: {len(risultati)}")
for r in risultati:
    print(f"  {r['originale']} -> {r['telegraph']}")
```

### Esempio 4: Uso avanzato con ArticleContent

```python
from src.core.extractor import estrai_contenuto_da_url

url = "https://example.com/article"
article = estrai_contenuto_da_url(url)

if article:
    # Accesso ai dati strutturati
    print(f"Titolo: {article.title}")
    print(f"Lunghezza testo: {len(article.text)} caratteri")
    
    # Conversione a dizionario
    data = article.to_dict()
    
    # Salvataggio in JSON
    import json
    with open("article.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Statistiche
    parole = len(article.text.split())
    print(f"Numero di parole: {parole}")
    print(f"Tempo di lettura stimato: {parole // 200} minuti")
```

## Test

I moduli principali includono esempi di test che possono essere eseguiti direttamente:

```bash
# Test del modulo extractor
python src/core/extractor.py

# Test del modulo scraper
python src/core/scraper.py

# Test del modulo summarizer
python src/core/summarizer.py
```

## Gestione Errori

Tutte le funzioni gestiscono gli errori in modo robusto:

- Restituiscono `None` in caso di errore
- Stampano messaggi di errore descrittivi
- Gestiscono timeout di rete
- Validano l'HTML prima della pubblicazione su Telegraph

## Note

- **Timeout**: Il timeout di default è 15 secondi, ma può essere personalizzato
- **User-Agent**: Viene usato un User-Agent standard per evitare blocchi
- **HTML Cleaning**: L'HTML viene automaticamente pulito e validato con BeautifulSoup
- **Metadati**: Non tutti i siti forniscono metadati completi; alcuni campi potrebbero essere `None`
