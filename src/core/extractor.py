"""
Modulo per l'estrazione di contenuti da URL utilizzando Trafilatura.
Fornisce funzioni per estrarre e formattare il contenuto in vari formati.
"""

import asyncio
import json
import os
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import aiohttp
import trafilatura
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from .http_config import get_random_headers


@dataclass
class ArticleContent:
    """Rappresenta il contenuto estratto da un articolo."""

    title: str
    text: str
    author: Optional[str] = None
    date: Optional[str] = None
    url: str = ""
    description: Optional[str] = None
    sitename: Optional[str] = None
    categories: Optional[list] = None
    tags: Optional[list] = None
    images: Optional[list] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte l'articolo in un dizionario."""
        return {
            "title": self.title,
            "text": self.text,
            "author": self.author,
            "date": self.date,
            "url": self.url,
            "description": self.description,
            "sitename": self.sitename,
            "categories": self.categories,
            "tags": self.tags,
            "images": self.images,
        }


async def _scrape_with_beautifulsoup(html_content: str) -> Optional[Dict[str, Any]]:
    """
    Estrae il contenuto da HTML usando BeautifulSoup come fallback.
    Versione più permissiva che estrae tutto il testo disponibile.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Rimuovi elementi non desiderati
        for element in soup(
            [
                "script",
                "style",
                "header",
                "footer",
                "nav",
                "aside",
                "iframe",
            ]
        ):
            element.decompose()

        # Prova diversi metodi per trovare il contenuto, dal più specifico al più generico
        article_body = None

        # 1. Cerca elementi article, main
        article_body = soup.find("article") or soup.find("main")

        # 2. Cerca div con classi comuni per contenuti
        if not article_body:
            article_body = soup.find(
                "div",
                class_=re.compile(
                    r"(post|content|article|text|body|entry|story|paragraph|reader)",
                    re.IGNORECASE,
                ),
            )

        # 3. Cerca per id comuni
        if not article_body:
            article_body = soup.find(
                "div",
                id=re.compile(
                    r"(post|content|article|text|body|entry|story|main)", re.IGNORECASE
                ),
            )

        # 4. Fallback: usa tutto il body
        if not article_body:
            article_body = soup.body

        # 5. Ultimo tentativo: usa tutta la pagina
        if not article_body:
            article_body = soup

        # Estrai tutto il testo disponibile, pulendo gli spazi
        text = " ".join(article_body.get_text(separator=" ", strip=True).split())

        # Estrai il titolo da più fonti possibili
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Cerca anche in meta tags
        if not title:
            meta_title = soup.find("meta", property="og:title") or soup.find(
                "meta", attrs={"name": "twitter:title"}
            )
            if meta_title and meta_title.get("content"):
                title = meta_title.get("content").strip()

        # Cerca in h1
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

        if not title:
            title = "Titolo non disponibile"

        # Ritorna anche se il testo è minimo - lascia che sia l'LLM a decidere
        if not text or len(text.strip()) < 10:
            return None

        return {"title": title, "text": text}
    except Exception as e:
        print(f"Errore durante lo scraping con BeautifulSoup: {e}")
        return None


async def _fetch_with_curl_cffi(url: str, timeout: int = 15) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Tenta di scaricare l'URL usando curl_cffi per bypassare controlli TLS/Bot.
    """
    print(f"Tentativo di fallback con curl_cffi per {url}...")
    try:
        # Usa 'chrome' come impersonazione sicura e moderna
        async with AsyncSession(impersonate="chrome") as session:
            response = await session.get(url, timeout=timeout)

            if response.status_code == 200:
                return response.content, None
            elif response.status_code in [403, 429]:
                return None, f"curl_cffi blocked with status {response.status_code}"
            else:
                return None, f"curl_cffi failed with status {response.status_code}"
    except Exception as e:
        return None, f"curl_cffi exception: {e}"


async def _fetch_with_flaresolverr(url: str, timeout: int = 60) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Attempts to download the URL using FlareSolverr (if configured).
    """
    flaresolverr_url = os.getenv("FLARESOLVERR_URL")
    if not flaresolverr_url:
        return None, "FlareSolverr not configured"

    print(f"Tentativo di fallback con FlareSolverr per {url}...")

    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": timeout * 1000  # FlareSolverr expects ms
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                flaresolverr_url,
                json=payload,
                timeout=timeout + 5
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ok":
                        # The HTML response is in solution.response
                        html_content = data.get("solution", {}).get("response")
                        if html_content:
                            return html_content.encode('utf-8'), None
                        else:
                            return None, "FlareSolverr returned 'ok' but no content"
                    else:
                        return None, f"FlareSolverr error: {data.get('message', 'Unknown error')}"
                else:
                    return None, f"FlareSolverr HTTP status: {response.status}"
    except Exception as e:
        return None, f"FlareSolverr exception: {e}"


async def scrape_article(
    url: str,
    timeout: int = 15,
    include_images: bool = True,
    include_links: bool = True,
) -> Tuple[Optional[ArticleContent], bool, Optional[str]]:
    """
    Estrae il contenuto principale da un URL, con fallback su BeautifulSoup e curl_cffi.
    """
    fallback_used = False
    max_retries = 3
    html_content = None
    last_error = None

    # 1. Tentativo principale con aiohttp
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                request_headers = get_random_headers()
                async with session.get(
                    url, timeout=timeout, ssl=False, headers=request_headers
                ) as response:
                    if response.status == 429:
                        if attempt < max_retries - 1:
                            wait_time = random.uniform(5, 10)
                            print(f"Attempt {attempt + 1}/{max_retries} failed (429). Retrying in {wait_time:.1f}s...")
                            await asyncio.sleep(wait_time)
                            continue

                    # Se otteniamo 403 o 429 persistente, interrompiamo per passare a curl_cffi
                    if response.status in [403, 429]:
                        last_error = f"HTTP {response.status}"
                        print(f"aiohttp bloccato con status {response.status}. Passaggio al fallback.")
                        break

                    response.raise_for_status()
                    html_content = await response.read()
                    last_error = None
                    break

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                # Non ritentiamo su errori di connessione se vogliamo provare curl_cffi
                break

    # 2. Fallback su curl_cffi se aiohttp ha fallito (per blocchi o errori)
    if not html_content:
        print(f"aiohttp fallito. Avvio procedura di fallback avanzata per {url}...")
        content, error = await _fetch_with_curl_cffi(url, timeout)
        if content:
            html_content = content
            last_error = None
            print("Fallback curl_cffi riuscito!")
        else:
            print(f"Anche curl_cffi ha fallito: {error}")
            last_error = error

    # 3. Fallback to FlareSolverr if curl_cffi also failed
    if not html_content and os.getenv("FLARESOLVERR_URL"):
        print(f"curl_cffi fallito. Avvio fallback FlareSolverr per {url}...")
        content, error = await _fetch_with_flaresolverr(url)
        if content:
            html_content = content
            last_error = None
            print("Fallback FlareSolverr riuscito!")
        else:
            print(f"Anche FlareSolverr ha fallito: {error}")
            last_error = error

    # Se ancora nessun contenuto, rinunciamo
    if not html_content:
        final_error = f"Impossibile recuperare il contenuto da '{url}'. Ultimo errore: {last_error}"
        print(f"ERROR: {final_error}")
        return None, fallback_used, final_error

    # 3. Estrazione con Trafilatura
    try:
        extracted_data = await asyncio.to_thread(
            trafilatura.bare_extraction,
            html_content,
            include_images=include_images,
            include_links=include_links,
            output_format="python",
            with_metadata=True,
        )
    except Exception as e:
        print(f"Errore durante l'esecuzione di Trafilatura: {e}")
        extracted_data = None

    article = None
    if extracted_data and extracted_data.text and len(extracted_data.text) > 50:
        article = ArticleContent(
            title=extracted_data.title or "Titolo non disponibile",
            text=extracted_data.text,
            author=extracted_data.author,
            date=extracted_data.date,
            url=url,
            description=extracted_data.description,
            sitename=extracted_data.sitename,
            categories=extracted_data.categories,
            tags=extracted_data.tags,
            images=[
                img.src
                for img in ([extracted_data.image] if extracted_data.image else [])
                if hasattr(img, "src") and img.src
            ],
        )
    else:
        # 4. Fallback BeautifulSoup
        print("Trafilatura insufficiente. Tentativo fallback BeautifulSoup...")
        fallback_used = True
        fallback_content = await _scrape_with_beautifulsoup(
            html_content.decode("utf-8", errors="ignore")
        )

        if fallback_content and fallback_content.get("text"):
            article = ArticleContent(
                title=fallback_content["title"],
                text=fallback_content["text"],
                url=url,
            )
        else:
            print("Anche il fallback BeautifulSoup ha fallito.")

    return article, fallback_used, None
