"""
Modulo per la generazione di riassunti di articoli web con LLM.
"""

import os
import re
from typing import Optional, List, Set

# Importa le classi necessarie
from extractor import ArticleContent
from openai import OpenAI, OpenAIError


# --- Funzioni di arricchimento (Placeholder) ---
# (Queste funzioni rimangono invariate)
def _enrich_with_web_search(query: str) -> Optional[str]:
    print(f"\\n--- Arricchimento: Ricerca web simulata per '{query}' ---")
    return f"Secondo una ricerca web simulata, l'argomento '{query}' è di grande attualità."

def _extract_keywords(text: str) -> List[str]:
    print("\\n--- Arricchimento: Estrazione parole chiave simulata ---")
    base_keywords = ["tecnologia", "innovazione", "sostenibilità"]
    words = re.findall(r'\\b\\w{5,}\\b', text.lower())
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
        title_words = re.findall(r'\\b\\w{4,}\\b', article.title.lower())
        candidates.update(title_words)
    keywords = _extract_keywords(article.text)
    candidates.update([kw.lower() for kw in keywords])

    hashtags: Set[str] = set()
    for cand in candidates:
        clean_tag = re.sub(r'[^a-zA-Z0-9]', '', cand)
        if clean_tag:
            hashtags.add(f"#{clean_tag}")

    return " ".join(list(hashtags)[:8])


# --- Funzione di chiamata all'LLM (Implementazione Reale) ---

def _call_llm_api(prompt: str) -> str:
    """
    Chiama l'API di OpenAI per generare un riassunto basato sul prompt.

    Questa funzione richiede che la variabile d'ambiente OPENAI_API_KEY sia impostata.

    Args:
        prompt: Il prompt completo da inviare al modello.

    Returns:
        Il riassunto generato, o un messaggio di errore.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "**ERRORE:** La variabile d'ambiente `OPENAI_API_KEY` non è stata impostata. "
            "Per favore, imposta la tua chiave API di OpenAI per continuare."
        )

    try:
        print("\\n--- Chiamata all'API di OpenAI in corso... ---")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Sei un assistente esperto nella sintesi di testi. Il tuo compito è seguire le istruzioni per riassumere l'articolo fornito.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=250,
        )
        print("--- Chiamata API completata con successo! ---")
        return response.choices[0].message.content.strip()

    except OpenAIError as e:
        print(f"--- ERRORE durante la chiamata all'API di OpenAI: {e} ---")
        return f"**ERRORE:** Impossibile completare la richiesta all'API di OpenAI. Dettagli: {e}"


# --- Funzione Principale ---
# (La logica principale rimane quasi invariata)
def summarize_article(
    article: ArticleContent,
    summary_type: str,
    prompts_dir: str = "src/prompts",
    enable_enrichment: bool = True,
    include_hashtags: bool = True,
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

    # Chiama l'API LLM
    summary = _call_llm_api(prompt)

    # Aggiungi hashtag
    if include_hashtags and "ERRORE:" not in summary:
        hashtags = generate_hashtags(article, summary)
        if hashtags:
            summary += f"\\n\\n---\\n**Hashtag:**\\n{hashtags}"

    return summary
