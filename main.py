import asyncio
import logging
from discord_bot.client import NovaClient
from config.settings import load_settings
from memory.database import Database
from tournaments.scanner import TournamentScanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

async def main():
    settings = load_settings()
    db = Database(settings.database_path)
    db.initialize()
    client = NovaClient(settings=settings, db=db)
    scanner = TournamentScanner(client, db, settings.tournament_category_id)
    client.tournament_scanner = scanner
    await client.start(settings.discord_token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
