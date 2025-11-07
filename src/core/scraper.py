"""
Modulo per l'orchestrazione dell'estrazione e del riassunto di articoli.
Contiene anche una funzione per pubblicare su Telegra.ph.
"""

import re
from typing import Optional
from telegraph import Telegraph
from telegraph.exceptions import TelegraphException
from markdown_it import MarkdownIt

# Import delle funzioni di estrazione e riassunto
import asyncio
from core.extractor import scrape_article
from core.summarizer import summarize_article


def sanitize_for_telegraph(html_content: str) -> str:
    """
    Sanifica l'HTML per Telegra.ph, sostituendo i tag non supportati.
    """
    # Sostituisce i tag <h2> con <h3>
    html_content = re.sub(
        r"<h2\b([^>]*)>", r"<h3\1>", html_content, flags=re.IGNORECASE
    )
    html_content = re.sub(r"</h2>", r"</h3>", html_content, flags=re.IGNORECASE)
    return html_content


def markdown_to_html(markdown_text: str) -> str:
    """
    Converte Markdown in HTML per Telegra.ph, rispettando i singoli a capo.
    """
    # Usa la libreria markdown-it per una conversione più robusta
    md = MarkdownIt("commonmark", {"breaks": True, "html": True})
    html = md.render(markdown_text)
    # Rimuove i tag <p> e </p> per un maggiore controllo sulla spaziatura
    html = html.replace("<p>", "").replace("</p>", "<br>")
    return html


async def crea_articolo_telegraph_with_content(
    title: str,
    content: str,
    author_name: Optional[str] = None,
    image_urls: Optional[list] = None,
    original_url: Optional[str] = None,
) -> Optional[str]:
    """
    Pubblica il contenuto (in Markdown) e le immagini su Telegra.ph in modo asincrono.
    """
    html_content = ""

    if image_urls:
        for url in image_urls:
            html_content += f"<figure><img src='{url}'></figure>"

    main_html_content = markdown_to_html(content)
    sanitized_content = sanitize_for_telegraph(main_html_content)
    html_content += sanitized_content

    if original_url:
        html_content += f'<hr><p><i>Fonte originale: <a href="{original_url}">{original_url}</a></i></p>'

    def _create_page_sync():
        try:
            telegraph = Telegraph()
            telegraph.create_account(short_name="Python Bot")
            response = telegraph.create_page(
                title=title,
                html_content=html_content,
                author_name=author_name or "Automation Bot",
            )
            return response["url"]
        except TelegraphException as e:
            print(f"Errore durante la pubblicazione su Telegra.ph: {e}")
            return None

    url_creato = await asyncio.to_thread(_create_page_sync)
    if url_creato:
        print(f"✓ Articolo creato con successo su Telegra.ph: {url_creato}")

    return url_creato


# --- ESEMPIO DI UTILIZZO DEL NUOVO MODULO SUMMARIZER ---
async def main():
    """Funzione principale per l'esempio asincrono."""
    URL_DI_PROVA = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    print("--- ESTRAZIONE CONTENUTO DALL'URL ---")
    print(f"URL: {URL_DI_PROVA}\n")

    # 1. Estrai il contenuto completo usando la nuova funzione asincrona
    article_content, fallback_used = await scrape_article(URL_DI_PROVA)

    if fallback_used:
        print(
            ">> ATTENZIONE: È stato utilizzato il fallback scraper (BeautifulSoup).\n"
        )

    if not article_content:
        print("Impossibile procedere. L'estrazione del contenuto è fallita.")
    else:
        print("✓ Estrazione completata:")
        print(f"  - Titolo: {article_content.title}")
        print(f"  - Autore: {article_content.author}")
        print(f"  - Sito: {article_content.sitename}\n")

        # 2. Genera diversi tipi di riassunti (simulato in modo sincrono per semplicità)
        print("--- GENERAZIONE RIASSUNTI (SIMULATA) ---\n")

        # Esempio 1: Riassunto in tre punti
        print("--- 1. Riassunto in tre punti (con arricchimento) ---")
        summary_three_points = await summarize_article(
            article_content,
            summary_type="three_point_summary",
            enable_enrichment=True,
        )
        if summary_three_points:
            print(f"\n**RISULTATO:**\n{summary_three_points}\n")

        # Esempio 2: Spiegazione per un bambino (senza arricchimento)
        print("--- 2. Spiegazione 'Come a un bambino' (senza arricchimento) ---")
        summary_eli5 = await summarize_article(
            article_content,
            summary_type="eli5_summary",
            enable_enrichment=False,
            include_hashtags=False,
        )
        if summary_eli5:
            print(f"\n**RISULTATO:**\n{summary_eli5}\n")

        # Esempio 3: Post per social media
        print("--- 3. Post per Social Media (con hashtag) ---")
        summary_social = await summarize_article(
            article_content,
            summary_type="social_media_post",
        )
        if summary_social:
            print(f"\n**RISULTATO:**\n{summary_social}\n")

        print("--- ESECUZIONE COMPLETATA ---")


if __name__ == "__main__":
    asyncio.run(main())
