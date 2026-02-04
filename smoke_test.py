"""Minimal smoke test (no Telegram token needed).

Run:
    python smoke_test.py

It checks:
- modules import
- db schema init + defaults (creates/opens BOT_DB or bot.db)
"""

import os
import asyncio

from dotenv import load_dotenv

import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_DB = os.getenv("BOT_DB", "bot.db")

async def main():
    await db.init_db(BOT_DB)
    print("OK: db.init_db")

if __name__ == "__main__":
    asyncio.run(main())
