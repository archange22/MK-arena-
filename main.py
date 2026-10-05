import asyncio
import logging
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

import config
from bot.client import ChachaBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("main")

class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Chacha Live Bot is running\n")

    def log_message(self, format, *args):
        pass

def run_health_server(port: int):
    try:
        server = HTTPServer(("0.0.0.0", port), HealthServer)
        logger.info(f"Serveur HTTP de santé démarré sur le port {port}.")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Impossible de démarrer le serveur de santé HTTP : {e}")

async def main():
    if not config.DISCORD_TOKEN:
        logger.critical("ERREUR CRITIQUE : DISCORD_TOKEN est absent ou vide.")
        logger.critical("Ajoutez la variable d'environnement DISCORD_TOKEN sur Render.")
        sys.exit(1)

    # Démarrage du serveur web de santé pour Render
    health_thread = threading.Thread(target=run_health_server, args=(config.PORT,), daemon=True)
    health_thread.start()

    bot = ChachaBot()
    async with bot:
        await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Arrêt du bot.")
