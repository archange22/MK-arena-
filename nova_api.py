# nova_api.py — à mettre dans ton bot (supprime ce fichier pour retirer l'API)
import os, aiohttp

NOVA_API_URL = os.getenv("NOVA_API_URL", "")   # ex: https://<ton-site>/api/public/bot/respond
NOVA_BOT_KEY = os.getenv("NOVA_BOT_KEY", "")

async def ask_nova_api(conversation_id: str, message: str, author: str = ""):
    if not NOVA_API_URL or not NOVA_BOT_KEY:
        return None  # API désactivée -> le bot utilise ses réponses locales
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                NOVA_API_URL,
                json={"conversation_id": conversation_id, "message": message, "author": author},
                headers={"x-api-key": NOVA_BOT_KEY},
                timeout=aiohttp.ClientTimeout(total=20)
            ) as r:
                if r.status == 200:
                    return (await r.json()).get("reply")
    except Exception:
        pass
    return None
