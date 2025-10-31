import re


def sanitize_html_for_telegram(text: str) -> str:
    """
    Sanitizes HTML to be compatible with Telegram's HTML parse mode.

    - Replaces paragraph tags (<p>) with double newlines.
    - Keeps only the allowed HTML tags (<b>, <i>, <u>, <s>, <blockquote>, <a>, <code>, <pre>).
    - Removes all other unsupported tags.
    """
    if not text:
        return ""

    # List of allowed tags for Telegram HTML parse mode
    # See: https://core.telegram.org/bots/api#html-style
    allowed_tags = [
        "b",
        "strong",
        "i",
        "em",
        "u",
        "ins",
        "s",
        "strike",
        "del",
        "blockquote",
        "a",
        "code",
        "pre",
        "tg-spoiler",
    ]

    # 1. Replace paragraph tags with newlines
    text = re.sub(r"<p>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)

    # 2. Build a regex to remove all tags that are NOT in the allowed list
    # This pattern matches any tag that is not one of the allowed ones.
    allowed_tags_pattern = "|".join(allowed_tags)
    unsupported_tags_pattern = re.compile(
        rf"</?(?!({allowed_tags_pattern})\b)[a-zA-Z0-9]+\b[^>]*>",
        re.IGNORECASE,
    )

    sanitized_text = re.sub(unsupported_tags_pattern, "", text)

    # 3. Clean up leading/trailing whitespaces
    return sanitized_text.strip()


def format_summary_text(text: str) -> str:
    """
    Formatta il testo del riassunto per renderlo più leggibile per Telegram.

    Features:
    - Aggiunge a capo dopo frasi complete
    - Preserva abbreviazioni comuni (Dr., MJ., Inc., etc.)
    - Preserva numeri decimali e elenchi puntati
    - Gestisce correttamente virgolette e parentesi
    - Rimuove spazi multipli e a capo eccessivi
    """
    if not text:
        return text

    # Lista di abbreviazioni comuni da preservare
    # Include titoli, iniziali, unità di misura, etc.
    abbreviations = [
        r"\b([A-Z])\.",  # Iniziali singole (M., J., K., etc.)
        r"\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr|Ph\.D|M\.D|Ing|Dott|Sig|Dott\.ssa)\.",  # Titoli
        r"\b(Inc|Ltd|Corp|Co|S\.p\.A|S\.r\.l)\.",  # Società
        r"\b(etc|vs|approx|e\.g|i\.e|cf|al|vol|ed)\.",  # Locuzioni latine/comuni
        r"\b([0-9]+)\.",  # Numeri seguiti da punto (elenchi, decimali)
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.",  # Mesi abbreviati
        r"\b(St|Ave|Blvd|Rd|Mt)\.",  # Abbreviazioni geografiche
    ]

    # Protezione temporanea delle abbreviazioni
    # Sostituisce il punto con un placeholder per evitare che venga interpretato come fine frase
    placeholder_map = {}
    placeholder_counter = 0

    for abbr_pattern in abbreviations:
        matches = re.finditer(abbr_pattern, text, re.IGNORECASE)
        for match in matches:
            placeholder = f"§§ABBR{placeholder_counter}§§"
            placeholder_map[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
            placeholder_counter += 1

    # Gestisce i casi di virgolette e parentesi prima della punteggiatura
    # Es: "Fine frase." diventa "Fine frase."\n
    text = re.sub(r'([.!?])(["\'»)])\s+', r"\1\2\n", text)

    # Aggiunge a capo dopo fine frase (. ! ?) seguita da spazio e maiuscola
    # Questo cattura le vere fine frase
    text = re.sub(r"([.!?])\s+(?=[A-Z])", r"\1\n", text)

    # Gestisce i punti di sospensione
    text = re.sub(r"(\.{3})\s+(?=[A-Z])", r"\1\n", text)

    # Ripristina le abbreviazioni
    for placeholder, original in placeholder_map.items():
        text = text.replace(placeholder, original)

    # Pulizia finale
    # Rimuove spazi multipli
    text = re.sub(r" +", " ", text)

    # Rimuove spazi prima della punteggiatura
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    # Rimuove a capo multipli (max 2 consecutivi)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Rimuove spazi all'inizio e fine delle righe
    text = "\n".join(line.strip() for line in text.split("\n"))

    # Trim generale
    return text.strip()
