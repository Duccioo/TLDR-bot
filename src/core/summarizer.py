"""
Module for generating article summaries using LLMs (Gemini, Groq, OpenRouter).
"""

import asyncio
import os
import re
import time
from typing import Optional, List, Set, Dict, Any
from dotenv import load_dotenv

# ---
from core.extractor import ArticleContent
from core.quota_manager import update_model_usage, wait_for_rate_limit, get_quota_data
from google import genai
from google.genai import types
from openai import OpenAI
from config import SUMMARY_LANGUAGE, GROQ_API_KEY, OPENROUTER_API_KEY

# Load environment variables from .env
load_dotenv()


def _extract_keywords(text: str) -> List[str]:
    print("\n--- Enrichment: Simulated Keyword Extraction ---")
    base_keywords = ["tecnologia", "innovazione", "sostenibility"]
    words = re.findall(r"\b\w{5,}\b", text.lower())
    if len(words) > 2:
        base_keywords.extend(words[:2])
    return base_keywords


def generate_hashtags(article: ArticleContent, summary_text: str) -> str:
    candidates: Set[str] = set()
    if article.tags:
        candidates.update([tag.lower() for tag in article.tags])
    if article.title:
        title_words = re.findall(r"\b\w{4,}\b", article.title.lower())
        candidates.update(title_words)
    keywords = _extract_keywords(article.text)
    candidates.update([kw.lower() for kw in keywords])

    hashtags: Set[str] = set()
    for cand in candidates:
        clean_tag = re.sub(r"[^a-zA-Z0-9]", "", cand)
        if clean_tag:
            hashtags.add(f"#{clean_tag}")

    return " ".join(list(hashtags)[:8])


def _clean_model_name(model_name: str) -> tuple[str, str]:
    """
    Strips provider prefix from model name if present.
    Returns (clean_model_name, provider).
    """
    if model_name.startswith("Gemini: "):
        return model_name.replace("Gemini: ", ""), "gemini"
    elif model_name.startswith("Groq: "):
        return model_name.replace("Groq: ", ""), "groq"
    elif model_name.startswith("OpenRouter: "):
        return model_name.replace("OpenRouter: ", ""), "openrouter"

    # Fallback/Legacy detection logic
    quota_data = get_quota_data()
    if model_name in quota_data.get("groq", {}):
        return model_name, "groq"
    elif model_name in quota_data.get("openrouter", {}):
        return model_name, "openrouter"

    return model_name, "gemini"  # Default


def _call_gemini_api(
    system_instruction: str,
    user_prompt: str,
    model_name: str,
    tools: Optional[List[types.Tool]] = None,
    max_retries: int = 4,
    temperature: float = 0.6,
    top_p: float = 0.95,
    top_k: int = 40,
) -> Dict[str, Any]:
    """Calls Google Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"summary": "**ERROR:** GEMINI_API_KEY not set.", "token_count": 0}

    retry_delays = [15, 30, 60]

    for attempt in range(max_retries):
        try:
            print(
                f"\n--- Attempt {attempt + 1}/{max_retries} calling Gemini ({model_name})... ---"
            )
            client = genai.Client(api_key=api_key)
            contents = [
                types.Content(
                    role="user", parts=[types.Part.from_text(text=user_prompt)]
                )
            ]

            generate_content_config = types.GenerateContentConfig(
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                system_instruction=[types.Part.from_text(text=system_instruction)],
            )
            if tools:
                generate_content_config.tools = tools

            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=generate_content_config,
            )

            summary_text = ""
            if hasattr(response, "text"):
                summary_text = response.text
            elif hasattr(response, "candidates") and response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text"):
                        summary_text += part.text

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
                print(f"--- Warning: Could not extract token count: {e} ---")

            print("--- API Call Success! ---")
            return {
                "summary": summary_text.strip(),
                "token_count": token_count,
                "provider": "gemini",
            }

        except Exception as e:
            if "503" in str(e) and "UNAVAILABLE" in str(e):
                if attempt < len(retry_delays):
                    delay = retry_delays[attempt]
                    print(f"--- ERROR 503 (Overloaded). Waiting {delay}s... ---")
                    time.sleep(delay)
                    continue
                else:
                    print("--- ERROR 503 Final failure. ---")
                    return {
                        "summary": f"**ERROR:** {e}",
                        "token_count": 0,
                        "needs_retry": True,
                    }
            else:
                print(f"--- Unrecoverable API Error: {e} ---")
                return {"summary": f"**ERROR:** {e}", "token_count": 0}
    return {"summary": "**ERROR:** Unexpected issue after retries.", "token_count": 0}


def _call_openai_compatible_api(
    system_instruction: str,
    user_prompt: str,
    model_name: str,
    provider: str,
    max_retries: int = 4,
    temperature: float = 0.6,
) -> Dict[str, Any]:
    """Calls OpenAI-compatible APIs (Groq, OpenRouter)."""
    from core.quota_manager import update_groq_rate_limits, update_openrouter_limits

    if provider == "groq":
        api_key = GROQ_API_KEY
        base_url = "https://api.groq.com/openai/v1"
    elif provider == "openrouter":
        api_key = OPENROUTER_API_KEY
        base_url = "https://openrouter.ai/api/v1"
    else:
        return {"summary": f"**ERROR:** Unknown provider {provider}", "token_count": 0}

    if not api_key:
        return {
            "summary": f"**ERROR:** {provider.upper()}_API_KEY not set.",
            "token_count": 0,
        }

    retry_delays = [15, 30, 60]

    for attempt in range(max_retries):
        try:
            print(
                f"\n--- Attempt {attempt + 1}/{max_retries} calling {provider} ({model_name})... ---"
            )
            client = OpenAI(api_key=api_key, base_url=base_url)

            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ]

            # Additional headers for OpenRouter
            extra_headers = {}
            if provider == "openrouter":
                extra_headers = {
                    "HTTP-Referer": "https://github.com/your-repo-url",  # Optional
                    "X-Title": "Telegram Summary Bot",  # Optional
                }

            # Use with_raw_response for Groq to capture rate limit headers
            if provider == "groq":
                raw_response = client.chat.completions.with_raw_response.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                )
                # Extract and save rate limit headers
                update_groq_rate_limits(model_name, dict(raw_response.headers))
                response = raw_response.parse()
            else:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    extra_headers=extra_headers if extra_headers else None,
                )
                # Update OpenRouter limits after successful call
                if provider == "openrouter":
                    update_openrouter_limits()

            summary_text = response.choices[0].message.content
            token_count = response.usage.total_tokens if response.usage else 0

            print("--- API Call Success! ---")
            return {
                "summary": summary_text.strip(),
                "token_count": token_count,
                "provider": provider,
            }

        except Exception as e:
            # Basic retry logic for rate limits or server errors
            if "429" in str(e) or "503" in str(e) or "500" in str(e):
                if attempt < len(retry_delays):
                    delay = retry_delays[attempt]
                    print(f"--- Error {e}. Waiting {delay}s... ---")
                    time.sleep(delay)
                    continue

            print(f"--- Unrecoverable API Error: {e} ---")
            return {"summary": f"**ERROR:** {e}", "token_count": 0}

    return {"summary": "**ERROR:** Unexpected issue after retries.", "token_count": 0}


def _call_llm_api(
    system_instruction: str,
    user_prompt: str,
    model_name: str,
    tools: Optional[List[types.Tool]] = None,
    max_retries: int = 4,
    temperature: float = 0.6,
    top_p: float = 0.95,
    top_k: int = 40,
) -> Dict[str, Any]:
    """
    Dispatcher function to call the appropriate LLM API based on the model name.
    """
    # Clean the model name and detect provider from prefix
    model_name, provider = _clean_model_name(model_name)

    if provider == "gemini":
        return _call_gemini_api(
            system_instruction,
            user_prompt,
            model_name,
            tools,
            max_retries,
            temperature,
            top_p,
            top_k,
        )
    else:
        # Groq/OpenRouter don't support Google Search tools in this implementation yet
        return _call_openai_compatible_api(
            system_instruction,
            user_prompt,
            model_name,
            provider,
            max_retries,
            temperature,
        )


async def summarize_article(
    article: ArticleContent,
    summary_type: str,
    prompts_dir: str = os.path.join("src", "prompts"),
    use_web_search: bool = False,
    use_url_context: bool = False,
    model_name: str = "gemini-2.5-flash",
) -> Optional[Dict[str, Any]]:
    """
    Orchestrates summary generation.
    """
    prompt_path = os.path.join(prompts_dir, f"{summary_type}.md")
    if not os.path.exists(prompt_path):
        print(f"Error: Prompt file not found: {prompt_path}")
        return None

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
    except IOError as e:
        print(f"Error reading prompt file: {e}")
        return None

    template = template.replace("{{summary_language}}", SUMMARY_LANGUAGE)

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

    # We need to clean model name here for rate limiting check too
    clean_model, provider = _clean_model_name(model_name)
    await asyncio.to_thread(wait_for_rate_limit, clean_model, provider)

    llm_response = await asyncio.to_thread(
        _call_llm_api,
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        model_name=model_name,  # Pass original with prefix, _call_llm_api cleans it again
        tools=tools or None,
    )

    summary_text = llm_response["summary"]
    token_count = llm_response["token_count"]
    # provider is returned by llm_response, but we already know it

    if "ERRORE:" not in summary_text and "ERROR:" not in summary_text:
        await asyncio.to_thread(update_model_usage, clean_model, token_count, provider)

    return {
        "summary": summary_text,
        "images": article.images,
    }


async def answer_question(
    article: ArticleContent,
    question: str,
    summary: str,
    model_name: str = "gemini-1.5-flash",
    prompts_dir: str = os.path.join("src", "prompts"),
) -> Optional[Dict[str, Any]]:
    """
    Asynchronously answers a user's question based on the article content.
    """
    prompt_path = os.path.join(prompts_dir, "qna.md")
    if not os.path.exists(prompt_path):
        print(f"Error: Prompt file not found: {prompt_path}")
        return None

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
    except IOError as e:
        print(f"Error reading prompt file: {e}")
        return None

    template = template.replace("{{summary_language}}", SUMMARY_LANGUAGE)

    if "---" in template:
        parts = template.split("---", 1)
        system_instruction = parts[0].strip()
        user_template = parts[1].strip()
    else:
        system_instruction = "You are a helpful assistant."
        user_template = template

    user_prompt = user_template.replace("{{title}}", article.title or "N/A")
    user_prompt = user_prompt.replace("{{url}}", article.url or "N/A")
    user_prompt = user_prompt.replace("{{summary}}", summary or "N/A")
    user_prompt = user_prompt.replace("{{text}}", article.text or "N/A")
    user_prompt = user_prompt.replace("{{question}}", question)

    tools = []

    clean_model, provider = _clean_model_name(model_name)
    await asyncio.to_thread(wait_for_rate_limit, clean_model, provider)

    llm_response = await asyncio.to_thread(
        _call_llm_api,
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        model_name=model_name,
        tools=tools or None,
    )

    answer_text = llm_response.get("summary", "")
    token_count = llm_response.get("token_count", 0)

    if "ERRORE:" not in answer_text and "ERROR:" not in answer_text:
        await asyncio.to_thread(update_model_usage, clean_model, token_count, provider)

    return {"summary": answer_text}
