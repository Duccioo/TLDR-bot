"""
Modulo per l'estrazione di contenuti da URL utilizzando Trafilatura.
Fornisce funzioni per estrarre e formattare il contenuto in vari formati.
"""

import asyncio
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import aiohttp
import trafilatura
from bs4 import BeautifulSoup

from .http_config import HEADERS, USER_AGENTS


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


async def scrape_article(
    url: str,
    timeout: int = 15,
    include_images: bool = True,
    include_links: bool = True,
) -> Tuple[Optional[ArticleContent], bool, Optional[str]]:
    """
    Estrae il contenuto principale da un URL, con fallback su BeautifulSoup.

    Args:
        url: L'URL dell'articolo.
        timeout: Timeout per la richiesta HTTP.
        include_images: Se includere le immagini.
        include_links: Se includere i link.

    Returns:
        Una tupla contenente:
        - Un oggetto ArticleContent o None.
        - Un booleano che indica se è stato usato il fallback (True se sì).
        - Una stringa con i dettagli dell'errore se il recupero fallisce, altrimenti None.
    """
    fallback_used = False
    max_retries = 3
    html_content = None
    last_error = None

    for attempt in range(max_retries):
        try:
            # Costruisce gli header per la richiesta in modo dinamico a ogni tentativo
            request_headers = HEADERS.copy()
            request_headers["User-Agent"] = random.choice(USER_AGENTS)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=timeout, ssl=False, headers=request_headers
                ) as response:
                    # Gestione specifica per l'errore 429
                    if response.status == 429:
                        if attempt < max_retries - 1:
                            wait_time = random.uniform(10, 15)
                            print(
                                f"Attempt {attempt + 1}/{max_retries} failed: 429 Too Many Requests. "
                                f"Retrying in {wait_time:.2f}s..."
                            )
                            await asyncio.sleep(wait_time)
                            continue  # Prossimo tentativo

                    response.raise_for_status()
                    html_content = await response.read()
                    last_error = None  # Resetta l'errore in caso di successo
                    break  # Esce dal ciclo se la richiesta ha successo

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_error = e
            # Interrompe i tentativi in caso di altri errori di connessione/timeout
            print(f"Attempt {attempt + 1}/{max_retries} failed with a connection error: {e}")
            break

    if last_error:
        error_details = f"Cannot reach URL '{url}' after attempts. Details: {last_error}"
        print(f"ERROR: {error_details}")
        return None, fallback_used, str(last_error)

    if not html_content:
        # Questo caso si verifica se tutti i tentativi falliscono con 429
        final_error = f"Failed to retrieve content from '{url}' after {max_retries} attempts due to 429 errors."
        print(f"ERROR: {final_error}")
        return None, fallback_used, final_error

    # 1. Prova con Trafilatura (eseguito in un thread per non bloccare)
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
    # Soglia minima ridotta per Trafilatura (da 150 a 50 caratteri)
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
        # 2. Se Trafilatura fallisce, usa il fallback BeautifulSoup
        print(
            "Trafilatura ha estratto poco o nessun testo. Tentativo di fallback con BeautifulSoup..."
        )
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
            print(
                f"BeautifulSoup ha estratto {len(fallback_content['text'])} caratteri di testo."
            )
        else:
            print(
                "Anche il fallback con BeautifulSoup non ha estratto contenuto sufficiente."
            )

    return article, fallback_used, None