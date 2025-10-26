# Modulo Summarizer - Documentazione

## Panoramica

Il modulo `summarizer.py` fornisce funzionalità per generare riassunti di articoli web utilizzando Google Gemini AI. Supporta prompt personalizzati, arricchimento del contesto e generazione automatica di hashtag.

## Configurazione

### Variabili d'Ambiente

Il modulo richiede la configurazione della seguente variabile d'ambiente nel file `.env`:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

**Come ottenere la chiave API:**
1. Visita [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Accedi con il tuo account Google
3. Crea una nuova API key
4. Copia la chiave nel file `.env`

### Modelli Disponibili

- **`gemini-1.5-flash`** (default): Veloce ed economico, ottimo per la maggior parte dei casi
- **`gemini-1.5-pro`**: Più potente e accurato, per compiti complessi
- **`gemini-pro`**: Versione stabile precedente

## Funzioni Principali

### `summarize_article()`

Genera un riassunto di un articolo utilizzando un prompt personalizzato.

```python
def summarize_article(
    article: ArticleContent,
    summary_type: str,
    prompts_dir: str = "src/prompts",
    enable_enrichment: bool = True,
    include_hashtags: bool = True,
    model_name: str = "gemini-1.5-flash",
) -> Optional[str]:
```

**Parametri:**

- `article` (ArticleContent): Oggetto contenente il contenuto dell'articolo estratto
- `summary_type` (str): Nome del file di prompt da utilizzare (senza estensione .md)
- `prompts_dir` (str): Directory contenente i file di prompt (default: "src/prompts")
- `enable_enrichment` (bool): Abilita l'arricchimento del contesto (default: True)
- `include_hashtags` (bool): Genera e include hashtag nel riassunto (default: True)
- `model_name` (str): Nome del modello Gemini da utilizzare (default: "gemini-1.5-flash")

**Restituisce:**
- `str`: Il riassunto generato con hashtag opzionali
- `None`: In caso di errore

**Esempio:**

```python
from src.extractor import estrai_contenuto_da_url
from src.summarizer import summarize_article

# Estrai l'articolo
article = estrai_contenuto_da_url("https://example.com/article")

# Genera un riassunto breve
summary = summarize_article(
    article=article,
    summary_type="brief",
    model_name="gemini-1.5-flash"
)

print(summary)
```

### `generate_hashtags()`

Genera hashtag rilevanti basati sul contenuto dell'articolo.

```python
def generate_hashtags(article: ArticleContent, summary_text: str) -> str:
```

**Parametri:**
- `article` (ArticleContent): L'articolo da cui estrarre gli hashtag
- `summary_text` (str): Il testo del riassunto (opzionale per analisi aggiuntiva)

**Restituisce:**
- `str`: Stringa con hashtag separati da spazi (massimo 8)

**Fonti degli hashtag:**
- Tag dell'articolo originale
- Parole chiave estratte dal titolo
- Parole significative dal testo (lunghezza > 4 caratteri)

**Esempio:**

```python
hashtags = generate_hashtags(article, summary_text)
print(hashtags)
# Output: #tecnologia #innovazione #AI #smartphone #google #android #mobile #tech
```

## Sistema di Prompt

### Struttura dei Prompt

I prompt sono file Markdown nella directory `src/prompts/` con segnaposto per i dati dell'articolo:

**Variabili disponibili:**
- `{{title}}` - Titolo dell'articolo
- `{{text}}` - Testo completo dell'articolo
- `{{author}}` - Autore dell'articolo
- `{{date}}` - Data di pubblicazione
- `{{url}}` - URL originale
- `{{sitename}}` - Nome del sito web

### Esempio di Prompt

**File: `src/prompts/brief.md`**

```markdown
Sei un esperto nella sintesi di articoli. Crea un riassunto conciso dell'articolo seguente.

**Titolo:** {{title}}
**Autore:** {{author}}
**Data:** {{date}}
**Fonte:** {{sitename}}

**Articolo:**
{{text}}

**Istruzioni:**
1. Riassumi l'articolo in massimo 3-4 frasi
2. Mantieni i punti chiave e le informazioni più importanti
3. Scrivi in modo chiaro e conciso
4. Usa un tono neutrale e professionale

**Riassunto:**
```

### Creazione di Nuovi Prompt

Per creare un nuovo tipo di riassunto:

1. Crea un nuovo file `.md` in `src/prompts/`
2. Usa le variabili `{{}}` per i dati dell'articolo
3. Definisci chiare istruzioni per il modello
4. Usa il nome del file (senza .md) come `summary_type`

**Esempio - Social Media Post:**

**File: `src/prompts/social.md`**

```markdown
Crea un post coinvolgente per i social media basato su questo articolo.

**Articolo:** {{title}}
{{text}}

**Istruzioni:**
1. Scrivi un post accattivante di massimo 280 caratteri
2. Usa un tono amichevole e coinvolgente
3. Includi una call-to-action
4. Non usare hashtag (verranno aggiunti automaticamente)

**Post:**
```

**Utilizzo:**

```python
summary = summarize_article(article, summary_type="social")
```

## Funzionalità Avanzate

### Arricchimento del Contesto

Il parametro `enable_enrichment` attiva funzionalità aggiuntive:

- **Ricerca web simulata**: Aggiunge contesto da ricerche web (attualmente placeholder)
- **Estrazione keyword**: Identifica parole chiave rilevanti nel testo
- **Analisi semantica**: Migliora la comprensione del contesto

```python
summary = summarize_article(
    article=article,
    summary_type="detailed",
    enable_enrichment=True  # Abilita arricchimento
)
```

### Configurazione del Modello

Personalizza i parametri del modello Gemini modificando la funzione `_call_llm_api()`:

```python
generation_config={
    "temperature": 0.7,      # Creatività (0.0-1.0)
    "top_p": 0.95,           # Nucleus sampling
    "top_k": 40,             # Top-k sampling
    "max_output_tokens": 2048,  # Lunghezza massima output
}
```

**Parametri:**

- `temperature`: Controlla la casualità (0 = deterministico, 1 = molto creativo)
- `top_p`: Nucleus sampling (0.9-0.95 consigliato)
- `top_k`: Limita alle top-k scelte più probabili
- `max_output_tokens`: Lunghezza massima della risposta

## Esempi Completi

### Esempio 1: Riassunto Semplice

```python
from src.extractor import estrai_contenuto_da_url
from src.summarizer import summarize_article

url = "https://example.com/article"
article = estrai_contenuto_da_url(url)

summary = summarize_article(
    article=article,
    summary_type="brief"
)

print(summary)
```

### Esempio 2: Riassunto per Social Media

```python
summary = summarize_article(
    article=article,
    summary_type="social",
    enable_enrichment=False,  # Non necessario per social
    include_hashtags=True,
    model_name="gemini-1.5-flash"
)

# Post su Twitter/X o altri social
print(summary)
```

### Esempio 3: Riassunto Dettagliato

```python
summary = summarize_article(
    article=article,
    summary_type="detailed",
    enable_enrichment=True,
    include_hashtags=False,  # Non serve per analisi dettagliate
    model_name="gemini-1.5-pro"  # Modello più potente
)

# Salva in un file
with open("summary.txt", "w", encoding="utf-8") as f:
    f.write(summary)
```

### Esempio 4: Batch Processing

```python
urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3"
]

summaries = []
for url in urls:
    article = estrai_contenuto_da_url(url)
    if article:
        summary = summarize_article(
            article=article,
            summary_type="brief"
        )
        summaries.append({
            "url": url,
            "title": article.title,
            "summary": summary
        })

# Salva tutti i riassunti
import json
with open("summaries.json", "w", encoding="utf-8") as f:
    json.dump(summaries, f, ensure_ascii=False, indent=2)
```

## Gestione Errori

Il modulo gestisce vari tipi di errori:

### API Key Mancante

```python
# Output:
# **ERRORE:** La variabile d'ambiente `GEMINI_API_KEY` non è stata impostata.
# Per favore, aggiungi la tua chiave API di Google Gemini al file .env:
# GEMINI_API_KEY=your_api_key_here
```

### Prompt Non Trovato

```python
# Output:
# Errore: Il file di prompt non esiste: src/prompts/nonexistent.md
```

### Errore API Gemini

```python
# Output:
# --- ERRORE durante la chiamata all'API di Google Gemini: [dettagli errore] ---
# **ERRORE:** Impossibile completare la richiesta all'API di Google Gemini. Dettagli: [...]
```

## Best Practices

1. **Usa il modello giusto:**
   - `gemini-1.5-flash` per riassunti veloci e quotidiani
   - `gemini-1.5-pro` per analisi approfondite

2. **Ottimizza i prompt:**
   - Sii specifico nelle istruzioni
   - Usa esempi se necessario
   - Testa e itera

3. **Gestisci i limiti:**
   - Verifica la lunghezza del testo input
   - Gestisci rate limits dell'API
   - Implementa retry logic se necessario

4. **Testa localmente:**
   - Usa articoli di test
   - Verifica la qualità degli output
   - Monitora i costi API

## Limiti e Considerazioni

- **Rate Limits**: Google Gemini ha limiti di richieste/minuto (varia per piano)
- **Token Limits**: Circa 30,000 token per richiesta (input + output)
- **Costi**: Il piano gratuito ha limitazioni; verifica i [prezzi](https://ai.google.dev/pricing)
- **Qualità**: I riassunti dipendono dalla qualità del prompt e dell'articolo originale

## Troubleshooting

### Problema: "API Key non valida"
**Soluzione:** Verifica che la chiave sia corretta e attiva su Google AI Studio

### Problema: "Rate limit exceeded"
**Soluzione:** Implementa pause tra le richieste o passa a un piano a pagamento

### Problema: "Riassunto di bassa qualità"
**Soluzione:** Migliora il prompt, aumenta la temperatura, o usa un modello più potente

### Problema: "Timeout"
**Soluzione:** Riduci la lunghezza dell'articolo o aumenta il timeout nelle richieste
