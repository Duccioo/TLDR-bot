"""
Modulo per la generazione di riassunti di articoli web con LLM.
Utilizza Google Gemini per la generazione dei riassunti.
"""

import os
import re
from typing import Optional, List, Set, Dict, Any
from dotenv import load_dotenv

# Importa le classi necessarie
from core.extractor import ArticleContent
from core.rate_limiter import wait_for_rate_limit
from core.quota_manager import update_model_usage
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
from google.generativeai import types as genai_types


def _call_llm_api(
    prompt: str,
    model_name: str = "gemini-1.5-flash",
    tools: Optional[List[genai_types.Tool]] = None,
) -> Dict[str, Any]:
    """
    Chiama l'API di Google Gemini per generare un riassunto basato sul prompt.

    Args:
        prompt: Il prompt completo da inviare al modello.
        model_name: Il nome del modello Gemini da utilizzare.
        tools: Una lista di tool da passare al modello (es. per la ricerca web).

    Returns:
        Un dizionario contenente il riassunto generato e il conteggio dei token,
        o un messaggio di errore.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "summary": "**ERRORE:** La variabile d'ambiente `GEMINI_API_KEY` non è stata impostata.",
            "token_count": 0,
        }

    try:
        print(f"\n--- Chiamata all'API di Google Gemini ({model_name}) in corso... ---")
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.6,
                "top_p": 0.95,
                "top_k": 40,
            },
        )

        response = model.generate_content(prompt, tools=tools)
        token_count = response.usage_metadata.total_token_count

        print("--- Chiamata API completata con successo! ---")
        return {"summary": response.text.strip(), "token_count": token_count}

    except Exception as e:
        print(f"--- ERRORE durante la chiamata all'API di Google Gemini: {e} ---")
        return {
            "summary": f"**ERRORE:** Impossibile completare la richiesta. Dettagli: {e}",
            "token_count": 0,
        }


# --- Funzione Principale ---
def summarize_article(
    article: ArticleContent,
    summary_type: str,
    prompts_dir: str = "src/bot/prompts",
    use_web_search: bool = False,
    use_url_context: bool = False,
    model_name: str = "gemini-1.5-flash",
) -> Optional[Dict[str, Any]]:
    prompt_path = os.path.join(prompts_dir, f"{summary_type}.md")
    if not os.path.exists(prompt_path):
        print(f"Errore: Il file di prompt non esiste: {prompt_path}")
        return None

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Popola il template
    prompt = template.replace("{{title}}", article.title or "N/A")
    prompt = prompt.replace("{{text}}", article.text or "N/A")
    prompt = prompt.replace("{{author}}", article.author or "N/A")
    prompt = prompt.replace("{{date}}", article.date or "N/A")
    prompt = prompt.replace("{{url}}", article.url or "N/A")
    prompt = prompt.replace("{{sitename}}", article.sitename or "N/A")

    # Configura i tool di Gemini
    tools = []
    if use_web_search:
        tools.append({"google_search": {}})
    if use_url_context and article.url:
        tools.append({"url_context": {}})
        prompt = f"Basandoti sul contenuto dell'URL {article.url}, {prompt}"

    # Attendi il rate limit
    wait_for_rate_limit(model_name)

    # Chiama l'API LLM
    llm_response = _call_llm_api(prompt, model_name=model_name, tools=tools or None)
    summary_text = llm_response["summary"]
    token_count = llm_response["token_count"]

    # Incrementa il contatore delle richieste
    if "ERRORE:" not in summary_text:
        update_model_usage(model_name, token_count)

    # Aggiungi hashtag solo se non ce ne sono già
    if "ERRORE:" not in summary_text and not article.tags:
        hashtags = generate_hashtags(article, summary_text)
        if hashtags:
            summary_text += f"\n\n---\n**Hashtag:**\n{hashtags}"

    return {
        "summary": summary_text,
        "images": article.images,
    }
