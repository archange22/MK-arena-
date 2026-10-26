import os
import logging
import re
import asyncio
from collections import defaultdict, deque

import aiohttp
import discord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("nova")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHATBOT_API_URL = os.getenv("CHATBOT_API_URL", "").strip()
CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY", "").strip()
CHATBOT_MODEL = os.getenv("CHATBOT_MODEL", "").strip()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Historique court, séparé par membre et salon.
histories = defaultdict(lambda: deque(maxlen=12))
last_reply_at = {}

SYSTEM_PROMPT = (
    "Tu es NOVA, un chatbot francophone amical pour une communauté Discord. "
    "Discute naturellement avec les membres sur des sujets variés. "
    "Tu n'es pas un expert des tournois et tu ne prétends pas gérer le serveur. "
    "Tu ne peux pas exécuter de commandes, modérer des membres ni changer les réglages. "
    "Si tu ne connais pas une information, dis-le clairement. "
    "Réponds de façon utile, concise et naturelle en français."
)


def local_reply(message: str) -> str:
    """Réponses de secours si aucun modèle génératif n'est configuré."""
    text = re.sub(r"\s+", " ", message.lower()).strip()
    if not text:
        return "Présent ! 😊 De quoi veux-tu parler ?"
    if any(word in text for word in ("bonjour", "salut", "hello", "bonsoir", "coucou", "yo")):
        return "Salut ! 😊 Je suis NOVA. Comment se passe ta journée ?"
    if any(phrase in text for phrase in ("qui es-tu", "tu es qui", "ton nom", "présente-toi")):
        return "Je suis NOVA, le chatbot de MK Arena. Pour le moment, mon mode local est limité, mais je suis là pour discuter avec toi. 🤖"
    if any(word in text for word in ("merci", "thanks", "bien joué", "bravo")):
        return "Avec plaisir ! 😊"
    if any(word in text for word in ("ça va", "comment vas-tu", "comment tu vas")):
        return "Ça roule côté NOVA ! 🤖 Et toi, comment tu vas ?"
    if any(word in text for word in ("blague", "fais-moi rire", "raconte une blague")):
        return "Pourquoi les programmeurs confondent-ils Halloween et Noël ? Parce que OCT 31 = DEC 25. 🎃"
    return (
        "Je t'écoute ! 😊 Mon mode actuel fonctionne sans modèle IA externe et ses réponses sont limitées. "
        "Pour une vraie conversation générative, il faut configurer un endpoint IA dans les variables d'environnement."
    )


async def generate_reply(prompt: str, key: tuple) -> str:
    history = histories[key]
    if CHATBOT_API_URL and CHATBOT_MODEL:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(list(history))
        messages.append({"role": "user", "content": prompt[:1800]})
        headers = {"Content-Type": "application/json"}
        if CHATBOT_API_KEY:
            headers["Authorization"] = f"Bearer {CHATBOT_API_KEY}"
        try:
            timeout = aiohttp.ClientTimeout(total=25)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    CHATBOT_API_URL,
                    headers=headers,
                    json={
                        "model": CHATBOT_MODEL,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 400,
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        answer = data["choices"][0]["message"]["content"].strip()
                        if answer:
                            history.append({"role": "user", "content": prompt[:1800]})
                            history.append({"role": "assistant", "content": answer[:1800]})
                            return answer[:1800]
                    else:
                        log.warning("Endpoint NOVA HTTP %s", response.status)
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, IndexError, TypeError, ValueError):
            log.warning("Endpoint NOVA indisponible, réponse locale utilisée.", exc_info=True)

    answer = local_reply(prompt)
    history.append({"role": "user", "content": prompt[:1800]})
    history.append({"role": "assistant", "content": answer[:1800]})
    return answer[:1800]


@client.event
async def on_ready():
    log.info("NOVA est connectée comme %s (%s)", client.user, client.user.id if client.user else "inconnu")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    content = message.content or ""
    mentions_bot = client.user is not None and client.user in message.mentions
    called_nova = re.search(r"\bnova\b", content, flags=re.IGNORECASE) is not None
    if not (mentions_bot or called_nova):
        return

    now = asyncio.get_running_loop().time()
    cooldown_key = (message.guild.id, message.author.id)
    if now - last_reply_at.get(cooldown_key, 0) < 3:
        return
    last_reply_at[cooldown_key] = now

    prompt = content
    if client.user:
        prompt = prompt.replace(f"<@{client.user.id}>", "").replace(f"<@!{client.user.id}>", "")
    prompt = re.sub(r"\bnova\b", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\s+", " ", prompt).strip(" ,.!?\n\t")
    if not prompt:
        prompt = "Présente-toi brièvement et demande-moi de quoi je veux parler."

    try:
        async with message.channel.typing():
            answer = await generate_reply(prompt, (message.guild.id, message.channel.id, message.author.id))
        await message.reply(answer[:1800], mention_author=False)
    except discord.DiscordException:
        log.exception("Impossible d'envoyer la réponse de NOVA")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("La variable DISCORD_TOKEN est absente. Ajoute-la dans les variables d'environnement de Render.")
    client.run(DISCORD_TOKEN, log_handler=None)
