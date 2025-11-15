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


def parse_hashtags(hashtag_string: str) -> list:
    """
    Extracts and cleans hashtags from a string.

    Handles various formats, including hashtags separated by spaces or commas.
    Filters out invalid elements (e.g., containing ':').

    Args:
        hashtag_string: The string from which to extract hashtags.

    Returns:
        A list of clean, formatted hashtags.
    """
    if not hashtag_string:
        return []

    # Replace commas with spaces to create a single delimiter
    normalized_string = hashtag_string.replace(",", " ")

    # Split the string into potential hashtags
    potential_tags = normalized_string.split()

    hashtags = set()  # Use a set to avoid duplicates
    for tag in potential_tags:
        # Discard invalid tags (e.g., 'pagetype:story')
        if ":" in tag:
            continue

        # Clean the tag
        cleaned_tag = tag.strip(" _#")

        # Replace spaces and other problematic characters with underscores
        cleaned_tag = re.sub(r'[\s\-.]+', '_', cleaned_tag)

        if cleaned_tag:
            hashtags.add(f"#{cleaned_tag}")

    return sorted(list(hashtags))  # Return a sorted list
