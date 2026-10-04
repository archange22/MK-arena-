import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from discord_bot.client import NovaClient
from config.settings import load_settings
from memory.database import Database
from tournaments.scanner import TournamentScanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("nova.main")


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"NOVA Bot MK Arena est en ligne !")

    def log_message(self, format, *args):
        # Silencer les pings HTTP de routine
        pass


def run_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Serveur HTTP de santé démarré sur le port {port} pour Render/Cloud")
    server.serve_forever()


async def main():
    # Démarre le serveur HTTP de santé en arrière-plan pour Render
    port_env = os.environ.get("PORT")
    if port_env:
        thread = threading.Thread(target=run_health_server, daemon=True)
        thread.start()

    logger.info("Chargement de la configuration...")
    settings = load_settings()
    
    logger.info("Initialisation de la base de données...")
    db = Database(settings.database_path)
    db.initialize()
    
    logger.info("Création du client NovaClient...")
    client = NovaClient(settings=settings, db=db)
    scanner = TournamentScanner(client, db, settings.tournament_category_id)
    client.tournament_scanner = scanner
    
    logger.info("Connexion à Discord...")
    await client.start(settings.discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Arrêt du bot par signal utilisateur.")
