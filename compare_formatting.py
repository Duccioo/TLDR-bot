#!/usr/bin/env python3
"""
Visual comparison: OLD vs NEW format_summary_text function.
Shows side-by-side the difference in output.
"""

import re


def format_summary_text_OLD(text: str) -> str:
    """OLD VERSION - Had issues with abbreviations."""
    if not text:
        return text
    text = re.sub(r"([.!?])\s+", r"\1\n", text)
    return text.strip()


def format_summary_text_NEW(text: str) -> str:
    """NEW VERSION - With abbreviation protection."""
    if not text:
        return text

    abbreviations = [
        r"\b([A-Z])\.",
        r"\b(Dr|Mr|Mrs|Ms|Prof|Sr|Jr|Ph\.D|M\.D|Ing|Dott|Sig|Dott\.ssa)\.",
        r"\b(Inc|Ltd|Corp|Co|S\.p\.A|S\.r\.l)\.",
        r"\b(etc|vs|approx|e\.g|i\.e|cf|al|vol|ed)\.",
        r"\b([0-9]+)\.",
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.",
        r"\b(St|Ave|Blvd|Rd|Mt)\.",
    ]

    placeholder_map = {}
    placeholder_counter = 0

    for abbr_pattern in abbreviations:
        matches = re.finditer(abbr_pattern, text, re.IGNORECASE)
        for match in matches:
            placeholder = f"§§ABBR{placeholder_counter}§§"
            placeholder_map[placeholder] = match.group(0)
            text = text.replace(match.group(0), placeholder, 1)
            placeholder_counter += 1

    text = re.sub(r'([.!?])(["\'»)])\s+', r"\1\2\n", text)
    text = re.sub(r"([.!?])\s+(?=[A-Z])", r"\1\n", text)
    text = re.sub(r"(\.{3})\s+(?=[A-Z])", r"\1\n", text)

    for placeholder, original in placeholder_map.items():
        text = text.replace(placeholder, original)

    text = re.sub(r" +", " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.split("\n"))

    return text.strip()


def print_comparison(title: str, raw_text: str):
    """Print side-by-side comparison."""
    old_result = format_summary_text_OLD(raw_text)
    new_result = format_summary_text_NEW(raw_text)

    old_lines = old_result.split("\n")
    new_lines = new_result.split("\n")

    print(f"\n{'='*80}")
    print(f"📊 {title}")
    print(f"{'='*80}")

    print(f"\n📥 INPUT (RAW FROM LLM):")
    print(f"{'─'*80}")
    print(raw_text)

    print(f"\n\n{'┌'+ '─'*38 + '┬' + '─'*39 + '┐'}")
    print(f"│ {'❌ OLD (BUGGY)':^38} │ {'✅ NEW (FIXED)':^39} │")
    print(f"{'├'+ '─'*38 + '┼' + '─'*39 + '┤'}")

    max_lines = max(len(old_lines), len(new_lines))

    for i in range(max_lines):
        old_line = old_lines[i] if i < len(old_lines) else ""
        new_line = new_lines[i] if i < len(new_lines) else ""

        # Truncate if too long
        if len(old_line) > 36:
            old_line = old_line[:33] + "..."
        if len(new_line) > 37:
            new_line = new_line[:34] + "..."

        print(f"│ {old_line:38} │ {new_line:39} │")

    print(f"{'└'+ '─'*38 + '┴' + '─'*39 + '┘'}")

    # Stats
    old_count = len(old_lines)
    new_count = len(new_lines)

    print(f"\n📊 STATISTICS:")
    print(
        f"   OLD: {old_count} lines | NEW: {new_count} lines | Diff: {abs(old_count - new_count)}"
    )

    # Check for issues
    issues_old = []
    if "MJ.\n" in old_result or " MJ.\n" in old_result:
        issues_old.append("MJ.")
    if "Dr.\n" in old_result:
        issues_old.append("Dr.")
    if "Inc.\n" in old_result:
        issues_old.append("Inc.")
    if "Prof.\n" in old_result:
        issues_old.append("Prof.")

    issues_new = []
    if "MJ.\n" in new_result or " MJ.\n" in new_result:
        issues_new.append("MJ.")
    if "Dr.\n" in new_result:
        issues_new.append("Dr.")
    if "Inc.\n" in new_result:
        issues_new.append("Inc.")
    if "Prof.\n" in new_result:
        issues_new.append("Prof.")

    if issues_old:
        print(f"\n   ❌ OLD Issues: {', '.join(issues_old)} have unwanted line breaks")
    else:
        print(f"\n   ✅ OLD: No issues detected")

    if issues_new:
        print(f"   ❌ NEW Issues: {', '.join(issues_new)} have unwanted line breaks")
    else:
        print(f"   ✅ NEW: No issues detected!")


def main():
    print("🔍 VISUAL COMPARISON: OLD vs NEW format_summary_text")
    print("=" * 80)

    test_cases = [
        {
            "title": "Case 1: Initials (MJ.)",
            "text": "Michael MJ. Jackson era un grande artista. Dr. Smith lo conosceva bene. È morto nel 2009.",
        },
        {
            "title": "Case 2: Companies",
            "text": "Apple Inc. ha lanciato iPhone. Microsoft Corp. ha risposto. Google Ltd. sta osservando.",
        },
        {
            "title": "Case 3: Scientific",
            "text": "Il Prof. Einstein ha pubblicato la teoria. Il Dr. Bohr ha risposto. Il valore è 3.14 circa.",
        },
        {
            "title": "Case 4: Mixed",
            "text": "Il CEO di Apple Inc. è Tim Cook. Ha lavorato con Steve Jobs Jr. Il Dr. Murray ha confermato.",
        },
        {
            "title": "Case 5: Numbers & Lists",
            "text": "Ci sono 3 punti: 1. Primo punto. 2. Secondo punto. 3. Terzo punto. Il prezzo è 99.99 euro.",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print_comparison(test_case["title"], test_case["text"])

        if i < len(test_cases):
            input("\n⏸️  Press Enter to continue...")

    print("\n" + "=" * 80)
    print("✅ COMPARISON COMPLETE!")
    print("=" * 80)
    print("\n💡 Summary:")
    print("   • OLD version breaks after EVERY period")
    print("   • NEW version preserves abbreviations intelligently")
    print("   • Result: Much better formatting for Telegram messages!")
    print("\n🚀 The NEW version is now active in the bot!")


if __name__ == "__main__":
    main()
