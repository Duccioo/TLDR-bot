"""
Modulo per la generazione di riassunti di articoli web con LLM.
Utilizza Google Gemini per la generazione dei riassunti.
"""

import os
import re
from typing import Optional, List, Set
from dotenv import load_dotenv

# Importa le classi necessarie
from core.extractor import ArticleContent
from core.rate_limiter import wait_for_rate_limit
from core.quota_manager import increment_request_count
import google.generativeai as genai

# Carica le variabili d'ambiente dal file .env
load_dotenv()


# --- Funzioni di arricchimento (Placeholder) ---
# (Queste funzioni rimangono invariate)
def _enrich_with_web_search(query: str) -> Optional[str]:
    print(f"\\n--- Arricchimento: Ricerca web simulata per '{query}' ---")
    return f"Secondo una ricerca web simulata, l'argomento '{query}' è di grande attualità."


def _extract_keywords(text: str) -> List[str]:
    print("\\n--- Arricchimento: Estrazione parole chiave simulata ---")
    base_keywords = ["tecnologia", "innovazione", "sostenibilità"]
    words = re.findall(r"\\b\\w{5,}\\b", text.lower())
    if len(words) > 2:
        base_keywords.extend(words[:2])
    return base_keywords


# --- Funzione di generazione Hashtag ---
# (Questa funzione rimane invariata)
def generate_hashtags(article: ArticleContent, summary_text: str) -> str:
    candidates: Set[str] = set()
    if article.tags:
        candidates.update([tag.lower() for tag in article.tags])
    if article.title:
        title_words = re.findall(r"\\b\\w{4,}\\b", article.title.lower())
        candidates.update(title_words)
    keywords = _extract_keywords(article.text)
    candidates.update([kw.lower() for kw in keywords])

    hashtags: Set[str] = set()
    for cand in candidates:
        clean_tag = re.sub(r"[^a-zA-Z0-9]", "", cand)
        if clean_tag:
            hashtags.add(f"#{clean_tag}")

    return " ".join(list(hashtags)[:8])


# --- Funzione di chiamata all'LLM (Implementazione con Google Gemini) ---


def _call_llm_api(prompt: str, model_name: str = "gemini-1.5-flash") -> str:
    """
    Chiama l'API di Google Gemini per generare un riassunto basato sul prompt.

    Questa funzione richiede che la variabile d'ambiente GEMINI_API_KEY sia impostata nel file .env.

    Args:
        prompt: Il prompt completo da inviare al modello.
        model_name: Il nome del modello Gemini da utilizzare (default: "gemini-1.5-flash").

    Returns:
        Il riassunto generato, o un messaggio di errore.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "**ERRORE:** La variabile d'ambiente `GEMINI_API_KEY` non è stata impostata. "
            "Per favore, aggiungi la tua chiave API di Google Gemini al file .env:\n"
            "GEMINI_API_KEY=your_api_key_here"
        )

    try:
        print(
            f"\\n--- Chiamata all'API di Google Gemini ({model_name}) in corso... ---"
        )

        # Configura l'API di Gemini
        genai.configure(api_key=api_key)

        # Crea il modello
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
        )

        # Genera il contenuto
        response = model.generate_content(prompt)

        print("--- Chiamata API completata con successo! ---")
        return response.text.strip()

    except Exception as e:
        print(f"--- ERRORE durante la chiamata all'API di Google Gemini: {e} ---")
        return f"**ERRORE:** Impossibile completare la richiesta all'API di Google Gemini. Dettagli: {e}"


# --- Funzione Principale ---
def summarize_article(
    article: ArticleContent,
    summary_type: str,
    prompts_dir: str = "src/bot/prompts",
    enable_enrichment: bool = True,
    include_hashtags: bool = True,
    model_name: str = "gemini-1.5-flash",
) -> Optional[str]:
    prompt_path = os.path.join(prompts_dir, f"{summary_type}.md")
    if not os.path.exists(prompt_path):
        print(f"Errore: Il file di prompt non esiste: {prompt_path}")
        return None

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    enrichment_context = ""
    if enable_enrichment:
        web_search_context = _enrich_with_web_search(article.title)
        if web_search_context:
            enrichment_context += f"\\n**Contesto aggiuntivo:** {web_search_context}\\n"

    # Popola il template
    prompt = template.replace("{{title}}", article.title or "N/A")
    prompt = prompt.replace("{{text}}", (article.text or "N/A") + enrichment_context)
    prompt = prompt.replace("{{author}}", article.author or "N/A")
    prompt = prompt.replace("{{date}}", article.date or "N/A")
    prompt = prompt.replace("{{url}}", article.url or "N/A")
    prompt = prompt.replace("{{sitename}}", article.sitename or "N/A")

    # Attendi il rate limit
    wait_for_rate_limit(model_name)

    # Chiama l'API LLM
    summary = _call_llm_api(prompt, model_name=model_name)

    # Incrementa il contatore delle richieste se la chiamata ha avuto successo
    if "ERRORE:" not in summary:
        increment_request_count(model_name)

    # Aggiungi hashtag
    if include_hashtags and "ERRORE:" not in summary:
        hashtags = generate_hashtags(article, summary)
        if hashtags:
            summary += f"\\n\\n---\\n**Hashtag:**\\n{hashtags}"

    return summary
