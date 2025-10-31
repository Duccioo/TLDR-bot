#!/usr/bin/env python3
"""
Quick comparison script to show the differences between old and new structure.
"""

import os


def count_lines(filepath):
    """Count lines in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception:
        return 0


def main():
    print("=" * 70)
    print("📊 TLDR-Bot Structure Comparison")
    print("=" * 70)

    # Old structure
    old_file = "src/telegram_bot.py"
    old_lines = count_lines(old_file)

    # New structure
    new_files = {
        "Core": "src/bot.py",
        "Config": "src/config.py",
        "Decorators": "src/decorators.py",
        "Keyboards": "src/keyboards.py",
        "Auth Handler": "src/handlers/auth_handlers.py",
        "Command Handler": "src/handlers/command_handlers.py",
        "Conversation Handler": "src/handlers/conversation_handlers.py",
        "Message Handler": "src/handlers/message_handlers.py",
        "Callback Handler": "src/handlers/callback_handlers.py",
    }

    print("\n🔴 OLD STRUCTURE (Monolithic)")
    print("-" * 70)
    print(f"  {old_file:45s} {old_lines:5d} lines")
    print(f"  {'TOTAL':45s} {old_lines:5d} lines")

    print("\n🟢 NEW STRUCTURE (Modular)")
    print("-" * 70)
    total_new = 0
    for name, filepath in new_files.items():
        lines = count_lines(filepath)
        total_new += lines
        status = "✅" if lines > 0 else "❌"
        print(f"  {status} {name:30s} ({filepath:32s}) {lines:4d} lines")

    print(f"\n  {'TOTAL':45s} {total_new:5d} lines")

    # Statistics
    print("\n" + "=" * 70)
    print("📈 STATISTICS")
    print("=" * 70)
    print(f"  Files in old structure:     1")
    print(f"  Files in new structure:     {len(new_files)}")
    print(f"  Average lines per file:     {total_new // len(new_files)}")
    print(
        f"  Largest file:               {max([count_lines(f) for f in new_files.values()])} lines"
    )
    print(
        f"  Smallest file:              {min([count_lines(f) for f in new_files.values()])} lines"
    )

    reduction = ((old_lines - (total_new // len(new_files))) / old_lines) * 100
    print(f"  Avg. file size reduction:   {reduction:.1f}%")

    # Benefits
    print("\n" + "=" * 70)
    print("✨ BENEFITS")
    print("=" * 70)
    benefits = [
        "✅ Separation of concerns",
        "✅ Easier to test individual modules",
        "✅ Reduced file size per module",
        "✅ Better code organization",
        "✅ Easier to locate specific functionality",
        "✅ Reduced merge conflicts in team work",
        "✅ More maintainable codebase",
        "✅ Easier to add new features",
        "✅ Better IDE navigation",
        "✅ Follows Python best practices",
    ]
    for benefit in benefits:
        print(f"  {benefit}")

    print("\n" + "=" * 70)
    print("🚀 Ready to use! Run: python src/bot.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
