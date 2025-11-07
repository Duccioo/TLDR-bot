import re
from typing import Tuple


def sanitize_html_for_telegram(text: str) -> str:
    """
    Sanitizes HTML to be compatible with Telegram's HTML parse mode.

    - Replaces paragraph tags (<p>) with newlines.
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

    # 1. Replace paragraph tags with double newlines for better readability
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
    - Rimuove introduzioni del LLM ("Certamente!", "Ecco il riassunto", etc.)
    - Preserva abbreviazioni comuni (Dr., MJ., Inc., etc.)
    - Preserva numeri decimali e elenchi puntati
    - Rimuove spazi multipli e a capo eccessivi
    """
    if not text:
        return text

    # FASE 1: Rimuove introduzioni comuni del LLM
    # Pattern di frasi introduttive da rimuovere
    intro_patterns = [
        r"^Certamente[!.]?\s*",
        r"^Certo[!.]?\s*",
        r"^Ecco\s+(a\s+te\s+)?il\s+riassunto[^.!?]*[.!?]\s*",
        r"^Ecco\s+(a\s+te\s+)?(un\s+)?riassunto[^.!?]*[.!?]\s*",
        r"^Ecco\s+a\s+te[^.!?]*[.!?]\s*",
        r"^Va\s+bene[!.]?\s*",
        r"^Perfetto[!.]?\s*",
        r"^D'accordo[!.]?\s*",
        r"^Fatto[!.]?\s*",
        r"^Fatto![!.]?\s*",
        r"^Ecco\s+fatto[!.]?\s*",
        r"^Ottimo[!.]?\s*",
        r"^Benissimo[!.]?\s*",
    ]

    # Applica tutti i pattern di rimozione
    for pattern in intro_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Rimuove righe vuote all'inizio
    text = text.lstrip()

    # # Lista di abbreviazioni comuni da preservare
    # # Include titoli, iniziali, unità di misura, etc.
    # abbreviations = [
    #     r"\b([A-Z])\.",  # Iniziali singole (M., J., K., etc.)
    #     r"\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr|Ph\.D|M\.D|Ing|Dott|Sig|Dott\.ssa)\.",  # Titoli
    #     r"\b(Inc|Ltd|Corp|Co|S\.p\.A|S\.r\.l)\.",  # Società
    #     r"\b(etc|vs|approx|e\.g|i\.e|cf|al|vol|ed)\.",  # Locuzioni latine/comuni
    #     r"\b([0-9]+)\.",  # Numeri seguiti da punto (elenchi, decimali)
    #     r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.",  # Mesi abbreviati
    #     r"\b(St|Ave|Blvd|Rd|Mt)\.",  # Abbreviazioni geografiche
    # ]

    # Protezione temporanea delle abbreviazioni
    # Sostituisce il punto con un placeholder per evitare che venga interpretato come fine frase
    # placeholder_map = {}
    # placeholder_counter = 0

    # for abbr_pattern in abbreviations:
    #     matches = re.finditer(abbr_pattern, text, re.IGNORECASE)
    #     for match in matches:
    #         placeholder = f"§§ABBR{placeholder_counter}§§"
    #         placeholder_map[placeholder] = match.group(0)
    #         text = text.replace(match.group(0), placeholder, 1)
    #         placeholder_counter += 1

    # # Ripristina le abbreviazioni
    # for placeholder, original in placeholder_map.items():
    #     text = text.replace(placeholder, original)

    # Pulizia finale
    # Rimuove spazi multipli
    # text = re.sub(r" +", " ", text)

    # # Rimuove spazi prima della punteggiatura
    # text = re.sub(r"\s+([,.!?;:])", r"\1", text)

    # # Rimuove spazi all'inizio e fine delle righe
    # text = "\n".join(line.strip() for line in text.split("\n"))

    # Rimuove righe vuote ma mantiene i singoli a capo
    lines = [line for line in text.split("\n") if line.strip()]

    # Se c'è più di un paragrafo, il primo viene reso in corsivo,
    # preservando l'emoji iniziale se presente.
    if len(lines) > 1:
        first_line = lines[0]
        emoji_match = re.match(r"^\s*(\S+)\s", first_line)
        if emoji_match:
            emoji = emoji_match.group(1)
            text_after_emoji = first_line[emoji_match.end(0) :].strip()
            if text_after_emoji and not (
                text_after_emoji.startswith("*") and text_after_emoji.endswith("*")
            ):
                lines[0] = f"{emoji} *{text_after_emoji}*"
            else:
                lines[0] = f"{emoji} {text_after_emoji}"
        else:
            stripped_first_line = first_line.strip()
            if stripped_first_line and not (
                stripped_first_line.startswith("*")
                and stripped_first_line.endswith("*")
            ):
                lines[0] = f"*{stripped_first_line}*"
            else:
                lines[0] = stripped_first_line

    # Unisce le righe con un singolo "a capo" per un testo più compatto
    text = "\n".join(lines)

    # Trim generale
    return text.strip()


def clean_hashtags_format(text: str) -> Tuple[str, str]:
    """
    Estrae e riposiziona gli hashtag da un blocco di testo Markdown.

    Rimuove eventuali sezioni del tipo
    "---\n**Hashtag:**\n#tag1 #tag2" e restituisce il testo pulito
    insieme alla stringa di hashtag trovati.
    """
    if not text:
        return text, ""

    working_text = text

    hashtag_patterns = [
        r"(?:\n|^)-{3,}\s*\n\*\*Hashtag:\*\*\s*\n(?P<tags>[\s\S]+?)(?:\n{2,}|\Z)",
        r"(?:\n|^)\*\*Hashtag:\*\*\s*\n(?P<tags>[\s\S]+?)(?:\n{2,}|\Z)",
        r"(?:\n|^)Hashtag:\s*\n(?P<tags>[\s\S]+?)(?:\n{2,}|\Z)",
    ]

    hashtags: list[str] = []

    def collect_hashtags(block: str) -> None:
        for candidate in re.findall(r"#\S+", block):
            cleaned = candidate.rstrip(".,;:!?)]}'\"")
            if len(cleaned) > 1 and cleaned not in hashtags:
                hashtags.append(cleaned)

    for pattern in hashtag_patterns:
        match = re.search(pattern, working_text, flags=re.IGNORECASE)
        if match:
            tags_block = match.group("tags")
            collect_hashtags(tags_block)
            working_text = working_text[: match.start()] + working_text[match.end() :]
            break

    if not hashtags:
        trailing_match = re.search(r"(?:\n|^)(#\S+(?:\s+#\S+)*)\s*$", working_text)
        if trailing_match:
            collect_hashtags(trailing_match.group(1))
            working_text = working_text[: trailing_match.start()]

    working_text = re.sub(r"\n?-{3,}\s*$", "", working_text).strip()
    working_text = re.sub(r"\n{3,}", "\n\n", working_text)

    hashtags_line = " ".join(hashtags)

    return working_text.strip(), hashtags_line
