"""
Modulo per l'estrazione di contenuti da URL utilizzando Trafilatura.
Fornisce funzioni per estrarre e formattare il contenuto in vari formati.
"""

import requests
import trafilatura
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime


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
        }


def estrai_contenuto_da_url(
    url: str,
    timeout: int = 15,
    include_images: bool = True,
    include_links: bool = True,
) -> Optional[ArticleContent]:
    """
    Estrae il contenuto principale da un URL utilizzando Trafilatura.

    Args:
        url: L'URL dell'articolo da cui estrarre il contenuto.
        timeout: Timeout per la richiesta HTTP in secondi (default: 15).
        include_images: Se includere le immagini nell'estrazione (default: True).
        include_links: Se includere i link nell'estrazione (default: True).

    Returns:
        Un oggetto ArticleContent con il contenuto estratto, o None in caso di errore.

    Example:
        >>> article = estrai_contenuto_da_url("https://example.com/article")
        >>> if article:
        ...     print(article.title)
        ...     print(article.text)
    """
    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore: Impossibile raggiungere l'URL '{url}'. Dettagli: {e}")
        return None

    # Estrai i metadati
    metadata = trafilatura.extract_metadata(response.content)

    # Estrai il testo principale
    text_content = trafilatura.extract(
        response.content,
        include_images=include_images,
        include_links=include_links,
        output_format="txt",
    )

    if not text_content:
        print("Errore: Trafilatura non è riuscito a estrarre contenuto significativo.")
        return None

    # Costruisci l'oggetto ArticleContent
    article = ArticleContent(
        title=(
            metadata.title if metadata and metadata.title else "Titolo non disponibile"
        ),
        text=text_content,
        author=metadata.author if metadata else None,
        date=metadata.date if metadata else None,
        url=url,
        description=metadata.description if metadata else None,
        sitename=metadata.sitename if metadata else None,
        categories=metadata.categories if metadata else None,
        tags=metadata.tags if metadata else None,
    )

    return article


def estrai_come_markdown(
    url: str,
    timeout: int = 15,
    include_metadata: bool = True,
) -> Optional[str]:
    """
    Estrae il contenuto da un URL e lo formatta in Markdown.

    Args:
        url: L'URL dell'articolo da cui estrarre il contenuto.
        timeout: Timeout per la richiesta HTTP in secondi (default: 15).
        include_metadata: Se includere i metadati nell'output (default: True).

    Returns:
        Una stringa in formato Markdown, o None in caso di errore.

    Example:
        >>> markdown = estrai_come_markdown("https://example.com/article")
        >>> if markdown:
        ...     with open("article.md", "w") as f:
        ...         f.write(markdown)
    """
    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore: Impossibile raggiungere l'URL '{url}'. Dettagli: {e}")
        return None

    # Estrai il contenuto in formato Markdown
    markdown_content = trafilatura.extract(
        response.content,
        include_images=True,
        include_links=True,
        output_format="markdown",
    )

    if not markdown_content:
        print("Errore: Trafilatura non è riuscito a estrarre contenuto significativo.")
        return None

    # Se richiesto, aggiungi i metadati in testa
    if include_metadata:
        metadata = trafilatura.extract_metadata(response.content)
        if metadata:
            header = []
            header.append("---")
            if metadata.title:
                header.append(f"# {metadata.title}")
                header.append("")
            if metadata.author:
                header.append(f"**Autore:** {metadata.author}")
            if metadata.date:
                header.append(f"**Data:** {metadata.date}")
            if metadata.sitename:
                header.append(f"**Fonte:** {metadata.sitename}")
            if metadata.description:
                header.append(f"\n_{metadata.description}_")
            header.append("")
            header.append(f"**URL originale:** {url}")
            header.append("---")
            header.append("")

            markdown_content = "\n".join(header) + "\n" + markdown_content

    return markdown_content


def estrai_come_html(
    url: str,
    timeout: int = 15,
    pulisci_html: bool = True,
) -> Optional[str]:
    """
    Estrae il contenuto da un URL e lo formatta in HTML pulito.

    Args:
        url: L'URL dell'articolo da cui estrarre il contenuto.
        timeout: Timeout per la richiesta HTTP in secondi (default: 15).
        pulisci_html: Se pulire l'HTML con BeautifulSoup (default: True).

    Returns:
        Una stringa HTML pulita, o None in caso di errore.

    Example:
        >>> html = estrai_come_html("https://example.com/article")
        >>> if html:
        ...     with open("article.html", "w") as f:
        ...         f.write(html)
    """
    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore: Impossibile raggiungere l'URL '{url}'. Dettagli: {e}")
        return None

    # Estrai il contenuto in formato HTML
    html_content = trafilatura.extract(
        response.content, include_images=True, include_links=True, output_format="html"
    )

    if not html_content:
        print("Errore: Trafilatura non è riuscito a estrarre contenuto significativo.")
        return None

    # Pulisci l'HTML se richiesto
    if pulisci_html:
        soup = BeautifulSoup(html_content, "html.parser")

        # Rimuovi i tag html, head e body se presenti
        for tag in soup.find_all(["html", "head", "body"]):
            tag.unwrap()

        html_content = str(soup).strip()

    return html_content


def estrai_metadati(url: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Estrae solo i metadati da un URL senza il contenuto completo.

    Args:
        url: L'URL da cui estrarre i metadati.
        timeout: Timeout per la richiesta HTTP in secondi (default: 15).

    Returns:
        Un dizionario con i metadati estratti, o None in caso di errore.

    Example:
        >>> metadata = estrai_metadati("https://example.com/article")
        >>> if metadata:
        ...     print(metadata['title'])
    """
    try:
        response = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Errore: Impossibile raggiungere l'URL '{url}'. Dettagli: {e}")
        return None

    metadata = trafilatura.extract_metadata(response.content)

    if not metadata:
        return None

    return {
        "title": metadata.title,
        "author": metadata.author,
        "date": metadata.date,
        "description": metadata.description,
        "sitename": metadata.sitename,
        "categories": metadata.categories,
        "tags": metadata.tags,
        "url": url,
    }


if __name__ == "__main__":
    # Test delle funzioni
    TEST_URL = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    print("=== Test estrazione contenuto ===")
    article = estrai_contenuto_da_url(TEST_URL)
    if article:
        print(f"Titolo: {article.title}")
        print(f"Autore: {article.author}")
        print(f"Data: {article.date}")
        print(f"Sito: {article.sitename}")
        print(f"Testo (primi 200 caratteri): {article.text[:200]}...")

    print("\n=== Test estrazione Markdown ===")
    markdown = estrai_come_markdown(TEST_URL)
    if markdown:
        print(f"Markdown (primi 300 caratteri):\n{markdown[:300]}...")

    print("\n=== Test estrazione HTML ===")
    html = estrai_come_html(TEST_URL)
    if html:
        print(f"HTML (primi 300 caratteri):\n{html[:300]}...")

    print("\n=== Test estrazione metadati ===")
    metadata = estrai_metadati(TEST_URL)
    if metadata:
        print("Metadati estratti:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
