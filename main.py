import asyncio
import logging
import os
import sys
import threading
from discord_bot.client import NovaClient
from config.settings import load_settings
from memory.database import Database
from tournaments.scanner import TournamentScanner
from dashboard.server import run_dashboard_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("nova.main")


async def main():
    logger.info("Démarrage de NOVA avec Panel d'Administration DraftBot...")
    
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        logger.error(
            "ERREUR CRITIQUE : La variable d environnement DISCORD_TOKEN est absente ou vide !\n"
            "Ajoutez DISCORD_TOKEN dans l onglet Environment de Render pour que le bot puisse se connecter."
        )
        # On lance quand même le dashboard en mode dégradé pour que Render valide le port HTTP
        port_env = os.environ.get("PORT", "10000")
        if port_env:
            try:
                port = int(port_env)
                thread = threading.Thread(target=run_dashboard_server, args=(port, None, None), daemon=True)
                thread.start()
            except ValueError:
                pass
        while True:
            await asyncio.sleep(60)

    try:
        settings = load_settings()
    except Exception as e:
        logger.error(f"Erreur lors du chargement des settings : {e}")
        while True:
            await asyncio.sleep(60)

    logger.info("Initialisation de la base de données...")
    db = Database(settings.database_path)
    db.initialize()

    logger.info("Initialisation du client NovaClient...")
    client = NovaClient(settings=settings, db=db)
    scanner = TournamentScanner(client, db, settings.tournament_category_id)
    client.tournament_scanner = scanner

    # Démarre le serveur Web Dashboard (Style DraftBot) sur $PORT
    port_env = os.environ.get("PORT", "10000")
    if port_env:
        try:
            port = int(port_env)
            thread = threading.Thread(target=run_dashboard_server, args=(port, client, db), daemon=True)
            thread.start()
            logger.info(f"Dashboard Web NOVA démarré sur le port {port}.")
        except ValueError:
            pass

    logger.info("Connexion en cours à Discord...")
    try:
        await client.start(settings.discord_token)
    except Exception as e:
        logger.exception(f"Erreur fatale lors de la connexion Discord : {e}")
        while True:
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt de NOVA.")
