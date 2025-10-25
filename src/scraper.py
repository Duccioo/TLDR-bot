"""
Modulo per la creazione e pubblicazione di articoli su Telegra.ph.
Utilizza il modulo extractor per l'estrazione del contenuto.
"""

# Assicurati di avere le librerie installate:
# pip install trafilatura requests python-telegraph beautifulsoup4

from typing import Optional
from telegraph import Telegraph
from telegraph.exceptions import TelegraphException

# Import delle funzioni di estrazione
from extractor import estrai_come_html, estrai_metadati


def crea_articolo_telegraph(
    url_articolo: str, author_name: Optional[str] = None
) -> Optional[str]:
    """
    Estrae il contenuto da un URL e lo pubblica su Telegra.ph.

    Args:
        url_articolo: L'URL dell'articolo di origine da cui estrarre i dati.
        author_name: Nome dell'autore da usare per la pubblicazione (opzionale).

    Returns:
        L'URL della pagina Telegra.ph appena creata in caso di successo,
        altrimenti None.
    """
    # Estrai i metadati
    metadata = estrai_metadati(url_articolo)
    if not metadata:
        print("Errore: Impossibile estrarre i metadati dall'URL.")
        return None

    # Estrai il contenuto HTML pulito
    html_content = estrai_come_html(url_articolo, pulisci_html=True)
    if not html_content:
        print("Errore: Impossibile estrarre il contenuto dall'URL.")
        return None

    # Determina il titolo e l'autore
    titolo = metadata.get("title", "Titolo non disponibile")
    autore = author_name or metadata.get("author") or "Python Automation Bot"

    # Pubblica su Telegraph
    try:
        telegraph = Telegraph()
        telegraph.create_account(short_name="Python Bot")

        response = telegraph.create_page(
            title=titolo,
            html_content=html_content,
            author_name=autore,
        )

        url_creato = response["url"]
        print(f"✓ Articolo creato con successo su Telegra.ph!")
        print(f"  Titolo: {titolo}")
        print(f"  Autore: {autore}")
        return url_creato

    except TelegraphException as e:
        print(f"Errore durante la pubblicazione su Telegra.ph: {e}")
        return None


# --- Esempio di utilizzo ---
if __name__ == "__main__":
    URL_DI_PROVA = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    print("=== Creazione articolo su Telegra.ph ===\n")
    # url_telegraph = crea_articolo_telegraph(URL_DI_PROVA)
    html_content = estrai_come_html(URL_DI_PROVA, pulisci_html=True)
    metadata = estrai_metadati(URL_DI_PROVA)

    print(html_content)

    print("**" * 20)
    if metadata:
        print(metadata)

    exit()

    if html_content:
        print(f"\n✓ Contenuto HTML estratto con successo!")
    else:
        print("\n✗ Errore durante l'estrazione del contenuto HTML.")
