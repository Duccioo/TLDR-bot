"""
Script di esempio per testare le funzionalità del TLDR-bot.
Dimostra l'estrazione, il riassunto e la pubblicazione di articoli.
"""

from src.core.extractor import estrai_contenuto_da_url, estrai_come_markdown, estrai_metadati
from src.core.scraper import crea_articolo_telegraph
from src.core.summarizer import summarize_article


def test_estrazione():
    """Test dell'estrazione di contenuti da un URL."""
    print("\n" + "=" * 60)
    print("TEST 1: Estrazione contenuto")
    print("=" * 60 + "\n")

    url = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    print(f"Estraendo contenuto da: {url}\n")

    # Estrai solo i metadati (veloce)
    metadata = estrai_metadati(url)
    if metadata:
        print("📋 Metadati estratti:")
        print(f"  Titolo: {metadata['title']}")
        print(f"  Autore: {metadata['author']}")
        print(f"  Data: {metadata['date']}")
        print(f"  Sito: {metadata['sitename']}")

    # Estrai il contenuto completo
    article = estrai_contenuto_da_url(url)
    if article:
        print(f"\n📄 Contenuto completo:")
        print(f"  Lunghezza testo: {len(article.text)} caratteri")
        print(f"  Parole: ~{len(article.text.split())} parole")
        print(f"\n  Anteprima (primi 200 caratteri):")
        print(f"  {article.text[:200]}...")
        return article

    return None


def test_markdown():
    """Test dell'estrazione in formato Markdown."""
    print("\n" + "=" * 60)
    print("TEST 2: Estrazione in Markdown")
    print("=" * 60 + "\n")

    url = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    markdown = estrai_come_markdown(url)
    if markdown:
        print("✓ Markdown generato con successo!")
        print(f"  Lunghezza: {len(markdown)} caratteri")
        print(f"\n  Anteprima (primi 400 caratteri):")
        print("-" * 60)
        print(markdown[:400] + "...")
        print("-" * 60)

        # Opzionalmente salva su file
        # with open("article.md", "w", encoding="utf-8") as f:
        #     f.write(markdown)
        # print("\n✓ Salvato in 'article.md'")


def test_riassunto(article):
    """Test della generazione di riassunti con Gemini."""
    print("\n" + "=" * 60)
    print("TEST 3: Generazione riassunto con Gemini")
    print("=" * 60 + "\n")

    if not article:
        print("⚠️  Nessun articolo da riassumere. Salta questo test.")
        return

    print("🤖 Generazione riassunto in corso...")
    print(f"   Articolo: {article.title}\n")

    # Nota: questo test richiede la GEMINI_API_KEY nel file .env
    summary = summarize_article(
        article=article,
        summary_type="one_paragraph_summary",  # Assicurati che questo prompt esista
        enable_enrichment=False,  # Disabilita per semplicità
        include_hashtags=True,
        model_name="gemini-1.5-flash",
    )

    if summary and "ERRORE:" not in summary:
        print("✓ Riassunto generato con successo!\n")
        print("-" * 60)
        print(summary)
        print("-" * 60)
    else:
        print("✗ Errore nella generazione del riassunto:")
        print(summary)


def test_telegraph():
    """Test della pubblicazione su Telegra.ph."""
    print("\n" + "=" * 60)
    print("TEST 4: Pubblicazione su Telegra.ph")
    print("=" * 60 + "\n")

    url = "https://www.ansa.it/sito/notizie/mondo/2025/10/19/rapina-al-louvre-rubati-i-gioielli-di-napoleone.-usato-un-montacarichi-panico-fra-i-visitatori_e12d06cd-8901-4ece-b295-b368a0786b5c.html"

    print(f"Pubblicando articolo da: {url}\n")

    telegraph_url = crea_articolo_telegraph(url, author_name="TLDR Bot")

    if telegraph_url:
        print(f"\n✓ Pubblicazione completata!")
        print(f"  URL Telegraph: {telegraph_url}")
        return telegraph_url
    else:
        print("\n✗ Errore durante la pubblicazione")

    return None


def main():
    """Esegue tutti i test."""
    print("\n" + "=" * 60)
    print("🤖 TLDR-BOT - Test Suite")
    print("=" * 60)

    # Test 1: Estrazione
    article = test_estrazione()

    # Test 2: Markdown
    test_markdown()

    # Test 3: Riassunto (richiede GEMINI_API_KEY)
    test_riassunto(article)

    # Test 4: Telegraph
    test_telegraph()

    print("\n" + "=" * 60)
    print("✓ Test completati!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
