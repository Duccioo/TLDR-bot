"""
Modulo per l'orchestrazione dell'estrazione e del riassunto di articoli.
Contiene anche una funzione per pubblicare su Telegra.ph.
"""

from typing import Optional
from telegraph import Telegraph
from telegraph.exceptions import TelegraphException

# Import delle funzioni di estrazione e riassunto
from core.extractor import estrai_contenuto_da_url, estrai_metadati, estrai_come_html
from core.summarizer import summarize_article


def crea_articolo_telegraph(
    url_articolo: str, author_name: Optional[str] = None
) -> Optional[str]:
    """
    Estrae il contenuto da un URL e lo pubblica su Telegra.ph.
    (Questa funzione rimane invariata, ma potrebbe essere usata in un flusso di lavoro)
    """
    metadata = estrai_metadati(url_articolo)
    if not metadata:
        print("Errore: Impossibile estrarre i metadati.")
        return None

    html_content = estrai_come_html(url_articolo, pulisci_html=True)
    if not html_content:
        print("Errore: Impossibile estrarre il contenuto.")
        return None

    titolo = metadata.get("title", "Titolo non disponibile")
    autore = author_name or metadata.get("author") or "Automation Bot"

    try:
        telegraph = Telegraph()
        telegraph.create_account(short_name="Python Bot")
        response = telegraph.create_page(
            title=titolo, html_content=html_content, author_name=autore
        )
        url_creato = response["url"]
        print(f"✓ Articolo creato con successo su Telegra.ph: {url_creato}")
        return url_creato
    except TelegraphException as e:
        print(f"Errore durante la pubblicazione su Telegra.ph: {e}")
        return None

def crea_articolo_telegraph_with_content(
    title: str,
    content: str,
    author_name: Optional[str] = None,
    image_urls: Optional[list] = None,
) -> Optional[str]:
    """
    Pubblica il contenuto e le immagini su Telegra.ph.
    """
    html_content = ""
    if image_urls:
        for url in image_urls:
            html_content += f"<img src='{url}'><br>"
    html_content += content

    try:
        telegraph = Telegraph()
        telegraph.create_account(short_name="Python Bot")
        response = telegraph.create_page(
            title=title,
            html_content=html_content,
            author_name=author_name or "Automation Bot",
        )
        url_creato = response["url"]
        print(f"✓ Articolo creato con successo su Telegra.ph: {url_creato}")
        return url_creato
    except TelegraphException as e:
        print(f"Errore durante la pubblicazione su Telegra.ph: {e}")
        return None

# --- ESEMPIO DI UTILIZZO DEL NUOVO MODULO SUMMARIZER ---
if __name__ == "__main__":
    URL_DI_PROVA = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    print(f"--- ESTRAZIONE CONTENUTO DALL'URL ---")
    print(f"URL: {URL_DI_PROVA}\\n")

    # 1. Estrai il contenuto completo usando la funzione da extractor.py
    article_content = estrai_contenuto_da_url(URL_DI_PROVA)

    if not article_content:
        print("Impossibile procedere. L'estrazione del contenuto è fallita.")
    else:
        print(f"✓ Estrazione completata:")
        print(f"  - Titolo: {article_content.title}")
        print(f"  - Autore: {article_content.author}")
        print(f"  - Sito: {article_content.sitename}\\n")

        # 2. Genera diversi tipi di riassunti
        print("--- GENERAZIONE RIASSUNTI (SIMULATA) ---\\n")

        # Esempio 1: Riassunto in tre punti
        print("--- 1. Riassunto in tre punti (con arricchimento) ---")
        summary_three_points = summarize_article(
            article_content,
            summary_type="three_point_summary",
            enable_enrichment=True,
        )
        if summary_three_points:
            print(f"\\n**RISULTATO:**\\n{summary_three_points}\\n")

        # Esempio 2: Spiegazione per un bambino (senza arricchimento)
        print("--- 2. Spiegazione 'Come a un bambino' (senza arricchimento) ---")
        summary_eli5 = summarize_article(
            article_content,
            summary_type="eli5_summary",
            enable_enrichment=False, # Disabilitiamo l'arricchimento per questo esempio
            include_hashtags=False # Disabilitiamo gli hashtag qui
        )
        if summary_eli5:
            print(f"\\n**RISULTATO:**\\n{summary_eli5}\\n")

        # Esempio 3: Post per social media
        print("--- 3. Post per Social Media (con hashtag) ---")
        summary_social = summarize_article(
            article_content,
            summary_type="social_media_post",
        )
        if summary_social:
            print(f"\\n**RISULTATO:**\\n{summary_social}\\n")

        print("--- ESECUZIONE COMPLETATA ---")
