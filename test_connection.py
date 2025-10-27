"""
Test script to verify Telegram bot connection.
"""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def test_bot():
    """Test bot connection."""
    if not TELEGRAM_BOT_TOKEN:
        print("✗ Error: TELEGRAM_BOT_TOKEN not set in .env file")
        return

    print(f"✓ Token found: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-5:]}")

    try:
        from telegram import Bot

        bot = Bot(token=TELEGRAM_BOT_TOKEN)

        print("Testing connection to Telegram...")
        me = await bot.get_me()

        print("✓ Connection successful!")
        print(f"  Bot username: @{me.username}")
        print(f"  Bot name: {me.first_name}")
        print(f"  Bot ID: {me.id}")

        # Test getting updates
        print("\nTesting updates...")
        updates = await bot.get_updates(limit=1)
        print(f"✓ Can receive updates (found {len(updates)} pending)")

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bot())
