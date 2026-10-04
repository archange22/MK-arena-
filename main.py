import asyncio
import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from discord_bot.client import NovaClient
from config.settings import load_settings
from memory.database import Database
from tournaments.scanner import TournamentScanner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("nova.main")


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"NOVA Bot MK Arena est en ligne !")

    def log_message(self, format, *args):
        pass


def run_health_server(port: int):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"Serveur HTTP de santé Render actif sur 0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Impossible de démarrer le serveur HTTP de santé : {e}")


async def main():
    # Démarre le serveur HTTP de santé si PORT est présent (Render Web Service)
    port_env = os.environ.get("PORT", "10000")
    if port_env:
        try:
            port = int(port_env)
            thread = threading.Thread(target=run_health_server, args=(port,), daemon=True)
            thread.start()
        except ValueError:
            pass

    logger.info("Démarrage de NOVA...")
    
    # Vérification explicite du token Discord
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        logger.error(
            "ERREUR CRITIQUE : La variable d environnement DISCORD_TOKEN est absente ou vide !\n"
            "Ajoutez DISCORD_TOKEN dans l onglet Environment de Render pour que le bot puisse se connecter."
        )
        # On maintient le processus en vie pour que Render affiche les logs au lieu de rebooter
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
