"""
Modulo per la generazione di riassunti di articoli web con LLM.
Utilizza Google Gemini per la generazione dei riassunti.
"""

import asyncio
import os
import re
import time
from typing import Optional, List, Set, Dict, Any
from dotenv import load_dotenv

# ---
from core.extractor import ArticleContent
from core.quota_manager import update_model_usage, wait_for_rate_limit
from google import genai
from google.genai import types

# Carica le variabili d'ambiente dal file .env
load_dotenv()


def _extract_keywords(text: str) -> List[str]:
    print("\\n--- Arricchimento: Estrazione parole chiave simulata ---")
    base_keywords = ["tecnologia", "innovazione", "sostenibility"]
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
    max_retries: int = 3,
    retry_delay: int = 15,
    temperature: float = 0.6,
    top_p: float = 0.95,
    top_k: int = 40,
) -> Dict[str, Any]:
    """
    Chiama l'API di Google Gemini per generare un riassunto basato sul prompt.
    Include un meccanismo di retry per errori 503.

    Args:
        system_instruction: Le istruzioni di sistema per il modello.
        user_prompt: Il prompt dell'utente con il contenuto dell'articolo.
        model_name: Il nome del modello Gemini da utilizzare.
        tools: Una lista di tool da passare al modello.
        max_retries: Numero massimo di tentativi.
        retry_delay: Secondi da attendere tra i tentativi.
        temperature: Parametro di temperatura per la generazione, che controlla la casualità.
        top_p: Parametro top_p per la generazione, ovvero la soglia di probabilità cumulativa.
        top_k: Parametro top_k per la generazione, ovvero il numero di token più probabili da considerare.

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

    for attempt in range(max_retries):
        try:
            print(
                f"\n--- Tentativo {attempt + 1}/{max_retries} di chiamata all'API di Google Gemini ({model_name})... ---"
            )

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
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                system_instruction=[
                    types.Part.from_text(text=system_instruction),
                ],
            )

            # Aggiungi tools alla configurazione se presenti
            if tools:
                generate_content_config.tools = tools

            # Genera il contenuto
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
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text"):
                        summary_text += part.text

            # Estrai il conteggio dei token in modo sicuro
            token_count = 0
            try:
                if hasattr(response, "usage_metadata"):
                    usage = response.usage_metadata
                    if hasattr(usage, "total_token_count"):
                        token_count = usage.total_token_count
                    elif hasattr(usage, "prompt_token_count") and hasattr(
                        usage, "candidates_token_count"
                    ):
                        token_count = (
                            usage.prompt_token_count + usage.candidates_token_count
                        )
            except AttributeError as e:
                print(
                    f"--- Avviso: Impossibile estrarre il conteggio dei token: {e} ---"
                )
                token_count = 0

            print("--- Chiamata API completata con successo! ---")
            return {"summary": summary_text.strip(), "token_count": token_count}

        except Exception as e:
            # Controlla se l'errore è un 503 Service Unavailable
            if "503" in str(e) and "UNAVAILABLE" in str(e):
                print(
                    f"--- ERRORE 503 (Model Overloaded) al tentativo {attempt + 1}. Attendo {retry_delay} secondi... ---"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue  # Riprova
                else:
                    print(
                        "--- Numero massimo di tentativi raggiunto. ERRORE DEFINITIVO. ---"
                    )
                    return {
                        "summary": f"**ERRORE:** Impossibile completare la richiesta. Dettagli: {e}",
                        "token_count": 0,
                    }
            else:
                # Se l'errore non è un 503, esci subito
                print(f"--- ERRORE non recuperabile durante la chiamata API: {e} ---")
                return {
                    "summary": f"**ERRORE:** Impossibile completare la richiesta. Dettagli: {e}",
                    "token_count": 0,
                }

    # Se il loop finisce senza successo (dovrebbe essere gestito sopra)
    return {
        "summary": "**ERRORE:** Si è verificato un problema imprevisto dopo tutti i tentativi.",
        "token_count": 0,
    }


# --- Funzione Principale ---
async def summarize_article(
    article: ArticleContent,
    summary_type: str,
    prompts_dir: str = os.path.join("src", "prompts"),
    use_web_search: bool = False,
    use_url_context: bool = False,
    model_name: str = "gemini-2.5-flash",
) -> Optional[Dict[str, Any]]:
    """
    Funzione asincrona per orchestrare la generazione del riassunto.
    """
    prompt_path = os.path.join(prompts_dir, f"{summary_type}.md")
    if not os.path.exists(prompt_path):
        print(f"Errore: Il file di prompt non esiste: {prompt_path}")
        return None

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
    except IOError as e:
        print(f"Errore nella lettura del file di prompt: {e}")
        return None

    if "**Contesto dell'articolo:**" in template:
        parts = template.split("**Contesto dell'articolo:**", 1)
        system_instruction = parts[0].strip()
        user_template = "**Contesto dell'articolo:**" + parts[1]
    else:
        system_instruction = template
        user_template = "**Contesto dell'articolo:**\n{{title}}\n{{text}}"

    user_prompt = user_template.replace("{{title}}", article.title or "N/A")
    user_prompt = user_prompt.replace("{{author}}", article.author or "N/A")
    user_prompt = user_prompt.replace("{{sitename}}", article.sitename or "N/A")
    user_prompt = user_prompt.replace("{{date}}", article.date or "N/A")
    user_prompt = user_prompt.replace(
        "{{tags}}", ", ".join(article.tags) if article.tags else "N/A"
    )
    user_prompt = user_prompt.replace("{{url}}", article.url or "N/A")
    user_prompt = user_prompt.replace("{{text}}", article.text or "N/A")

    tools = []
    if use_web_search:
        tools.append(types.Tool(googleSearch=types.GoogleSearch()))
    if use_url_context and article.url:
        user_prompt = f"Basandoti sul contenuto dell'URL {article.url}, {user_prompt}"

    # Esegui le operazioni bloccanti in un thread separato
    await asyncio.to_thread(wait_for_rate_limit, model_name)

    llm_response = await asyncio.to_thread(
        _call_llm_api,
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        model_name=model_name,
        tools=tools or None,
    )

    summary_text = llm_response["summary"]
    token_count = llm_response["token_count"]

    if "ERRORE:" not in summary_text:
        await asyncio.to_thread(update_model_usage, model_name, token_count)

    return {
        "summary": summary_text,
        "images": article.images,
    }
