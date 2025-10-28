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
from google import genai
from google.genai import types

# Carica le variabili d'ambiente dal file .env
load_dotenv()


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


def _call_llm_api(
    system_instruction: str,
    user_prompt: str,
    model_name: str = "gemini-1.5-flash",
    tools: Optional[List[types.Tool]] = None,
) -> Dict[str, Any]:
    """
    Chiama l'API di Google Gemini per generare un riassunto basato sul prompt.

    Args:
        system_instruction: Le istruzioni di sistema per il modello (ruolo e comportamento).
        user_prompt: Il prompt dell'utente con il contenuto dell'articolo.
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

        # Crea il client con il nuovo SDK
        client = genai.Client(api_key=api_key)

        # Prepara i contenuti dell'utente
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_prompt),
                ],
            ),
        ]

        # Prepara la configurazione
        generate_content_config = types.GenerateContentConfig(
            temperature=0.6,
            top_p=0.95,
            top_k=40,
            system_instruction=[
                types.Part.from_text(text=system_instruction),
            ],
        )

        # Aggiungi tools alla configurazione se presenti
        if tools:
            generate_content_config.tools = tools

        # Genera il contenuto (non in streaming)
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )

        # Estrai il testo e il conteggio dei token
        summary_text = ""
        if hasattr(response, "text"):
            summary_text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            # Estrai il testo dal primo candidato
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text"):
                    summary_text += part.text

        token_count = 0
        if hasattr(response, "usage_metadata"):
            token_count = response.usage_metadata.total_token_count

        print("--- Chiamata API completata con successo! ---")
        return {"summary": summary_text.strip(), "token_count": token_count}

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
    prompts_dir: str = os.path.join("src", "prompts"),
    use_web_search: bool = False,
    use_url_context: bool = False,
    model_name: str = "gemini-2.5-flash",
) -> Optional[Dict[str, Any]]:
    prompt_path = os.path.join(prompts_dir, f"{summary_type}.md")
    if not os.path.exists(prompt_path):
        print(f"Errore: Il file di prompt non esiste: {prompt_path}")
        return None

    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Separa il template in system instruction e user prompt
    # La parte prima di "**Contesto dell'articolo:**" è la system instruction
    # La parte dopo è il user prompt con i dati dell'articolo
    if "**Contesto dell'articolo:**" in template:
        system_instruction = template.split("**Contesto dell'articolo:**")[0].strip()
        user_template = (
            "**Contesto dell'articolo:**"
            + template.split("**Contesto dell'articolo:**")[1]
        )
    else:
        # Fallback: usa tutto come system instruction e crea un user prompt semplice
        system_instruction = template
        user_template = "**Contesto dell'articolo:**\n{{title}}\n{{text}}"

    # Popola il user prompt con i dati dell'articolo
    user_prompt = user_template.replace("{{title}}", article.title or "N/A")
    user_prompt = user_prompt.replace("{{text}}", article.text or "N/A")
    user_prompt = user_prompt.replace("{{author}}", article.author or "N/A")
    user_prompt = user_prompt.replace("{{date}}", article.date or "N/A")
    user_prompt = user_prompt.replace("{{url}}", article.url or "N/A")
    user_prompt = user_prompt.replace("{{sitename}}", article.sitename or "N/A")
    user_prompt = user_prompt.replace(
        "{{tags}}", ", ".join(article.tags) if article.tags else "N/A"
    )

    # Configura i tool di Gemini
    tools = []
    if use_web_search:
        # Usa il nuovo formato del SDK google-genai
        tools.append(types.Tool(googleSearch=types.GoogleSearch()))
    if use_url_context and article.url:
        user_prompt = f"Basandoti sul contenuto dell'URL {article.url}, {user_prompt}"

    # Attendi il rate limit
    wait_for_rate_limit(model_name)

    # Chiama l'API LLM
    llm_response = _call_llm_api(
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        model_name=model_name,
        tools=tools or None,
    )
    print("LLM response received, extracting summary...", flush=True)
    summary_text = llm_response["summary"]
    token_count = llm_response["token_count"]
    print(f"Summary extracted, tokens: {token_count}", flush=True)

    # Incrementa il contatore delle richieste
    if "ERRORE:" not in summary_text:
        print("Updating model usage...", flush=True)
        update_model_usage(model_name, token_count)
        print("Model usage updated", flush=True)

    # Aggiungi hashtag solo se non ce ne sono già
    print(f"Checking hashtags... (has tags: {bool(article.tags)})", flush=True)
    if "ERRORE:" not in summary_text and not article.tags:
        print("Generating hashtags...", flush=True)
        hashtags = generate_hashtags(article, summary_text)
        print(f"Hashtags generated: {hashtags[:50]}...", flush=True)
        if hashtags:
            summary_text += f"\n\n---\n**Hashtag:**\n{hashtags}"

    print("Returning summary data", flush=True)
    return {
        "summary": summary_text,
        "images": article.images,
    }
