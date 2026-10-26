import os
import logging
import re
import asyncio
import unicodedata
from collections import defaultdict, deque

import aiohttp
import discord

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("nova")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHATBOT_API_URL = os.getenv(
    "CHATBOT_API_URL", "https://api.groq.com/openai/v1/chat/completions"
).strip()
CHATBOT_API_KEY = os.getenv("GROQ_API_KEY", os.getenv("CHATBOT_API_KEY", "")).strip()
CHATBOT_MODEL = os.getenv("CHATBOT_MODEL", "openai/gpt-oss-20b").strip()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Historique court, séparé par membre et salon.
histories = defaultdict(lambda: deque(maxlen=12))
last_reply_at = {}
# Anti-doublon : empêche de traiter deux fois le même message Discord.
processed_message_ids = deque(maxlen=5000)
processed_message_id_set = set()

SYSTEM_PROMPT = (
    "Tu es NOVA, un chatbot francophone amical pour une communauté Discord. "
    "Discute naturellement avec les membres sur des sujets variés. "
    "Tu n'es pas un expert des tournois et tu ne prétends pas gérer le serveur. "
    "Tu ne peux pas exécuter de commandes, modérer des membres ni changer les réglages. "
    "Si tu ne connais pas une information, dis-le clairement. "
    "Réponds de façon utile, concise et naturelle en français."
)


def normalize_text(value: str) -> str:
    """Normalise accents et espaces pour mieux reconnaître le français informel."""
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9\s']", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def has_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Recherche des expressions entières, sans confondre des mots partiels."""
    return any(
        re.search(r"(?<!\w)" + re.escape(normalize_text(phrase)) + r"(?!\w)", text)
        for phrase in phrases
    )


def local_reply(message: str, history=None) -> str:
    """Petit moteur local par intentions : sans clé ni appel à une API externe."""
    raw = re.sub(r"\s+", " ", message).strip()
    text = normalize_text(raw)
    words = set(text.split())

    if not text:
        return "Je suis là 😊 Dis-moi ce que tu as en tête."

    # Salutations et présentations
    if has_any(text, ("qui es tu", "tu es qui", "c'est quoi nova", "ton nom", "presente toi", "presente toi")):
        return "Je suis NOVA, le chatbot de MK Arena 🤖. Je peux discuter, expliquer des idées et t'aider à réfléchir. Pour l'instant, je fonctionne sans modèle IA externe, donc mes connaissances restent limitées."
    if has_any(text, ("bonjour", "salut", "hello", "bonsoir", "coucou", "yo", "wesh")):
        return "Salut ! 😊 Quoi de neuf ? Tu veux parler de quoi ?"
    if has_any(text, ("ca va", "comment vas tu", "comment tu vas", "tu vas bien")):
        return "Ça va bien côté NOVA 🤖 Merci de demander ! Et toi, comment ça se passe ?"
    if has_any(text, ("merci", "thanks", "bien joue", "bravo")):
        return "Avec plaisir ! 😊"
    if has_any(text, ("au revoir", "a plus", "bonne nuit", "a demain", "je dois partir")):
        return "À plus ! 👋 Je serai là quand tu voudras reprendre la discussion."

    # Comprendre ce que la personne attend de NOVA
    if has_any(text, ("que peux tu faire", "tu sais faire quoi", "aide moi", "aide moi stp", "comment tu fonctionnes")):
        return "Je peux discuter, proposer des idées, expliquer un sujet et t'aider à organiser un projet. Je suis encore en mode local : je reconnais plusieurs intentions, mais je n'ai pas encore la compréhension générale d'un grand modèle IA."
    if has_any(text, ("tu comprends", "tu comprends rien", "tu es bete", "tu es nul")):
        return "Je suis encore en apprentissage côté code 😅 Sans moteur IA externe, je comprends surtout les intentions que mes règles reconnaissent. Reformule avec un peu de contexte et je vais essayer de mieux cibler ta demande."
    if has_any(text, ("repete", "redis", "qu'est ce que tu viens de dire", "tu as dit quoi")):
        if history:
            previous = next((item.get("content", "") for item in reversed(history) if item.get("role") == "assistant"), "")
            if previous:
                return "Ma réponse précédente était : " + previous[:900]
        return "Je n'ai pas encore de réponse précédente à répéter dans cette conversation."

    # Conversation générale
    if has_any(text, ("blague", "fais moi rire", "raconte une blague")):
        return "Pourquoi les programmeurs confondent-ils Halloween et Noël ? Parce que OCT 31 = DEC 25. 🎃"
    if has_any(text, ("je m'ennuie", "je m'ennuie", "ennuye", "je sais pas quoi faire")):
        return "On peut trouver un truc sympa 😊 Tu préfères discuter, inventer une idée, parler de jeux vidéo ou faire un petit quiz ?"
    if has_any(text, ("je suis triste", "pas le moral", "je vais mal", "je suis stresse", "je suis stressé")):
        return "Désolé que tu traverses ça. 💛 Tu veux me raconter ce qui se passe ? Je peux t'écouter et t'aider à mettre les choses au clair."
    if has_any(text, ("tu es une ia", "tu es un robot", "tu es humain", "tu es humaine")):
        return "Je suis un bot logiciel, pas une personne. 🤖 Pour le moment, mes réponses viennent de règles locales plutôt que d'un modèle génératif."
    if has_any(text, ("pourquoi", "comment", "explique", "c'est quoi", "qu'est ce que", "definition")):
        topic = raw[:180].strip()
        return (
            f"Tu veux comprendre : « {topic} ». Je vois le type de question, mais mon mode local ne possède pas encore assez de connaissances pour expliquer correctement tous les sujets. "
            "Donne-moi un peu plus de contexte, ou un choix précis, et je tenterai de t'orienter sans inventer une réponse."
        )

    # Détection de thèmes pour éviter une réponse identique à chaque fois.
    if has_any(text, ("codm", "call of duty", "mobile", "blood strike", "free fire", "jeu", "gaming", "game")):
        return "Tu parles de jeux vidéo 🎮. Tu veux plutôt des conseils pour progresser, parler d'un jeu précis ou trouver une idée de défi ?"
    if has_any(text, ("ecole", "devoir", "cours", "exercice", "revision", "examen")):
        return "On peut travailler sur ça 📚. Envoie la consigne ou dis-moi la matière, et je t'aiderai à découper le problème étape par étape."
    if has_any(text, ("discord", "serveur", "salon", "role", "bot")):
        return "Pour Discord, je peux t'aider à réfléchir à l'organisation du serveur ou au comportement du bot. Tu veux parler de quel élément exactement ?"
    if has_any(text, ("site web", "application", "programmer", "code", "github", "developper", "developpement", "ia")):
        return "Tu parles de création numérique 💻. Tu veux concevoir une idée, comprendre du code ou corriger un problème ? Donne-moi le détail important."
    if has_any(text, ("oui", "exact", "c'est ca", "voila", "d'accord", "ok")):
        return "D'accord 😊. Dis-moi ce que tu veux faire ensuite."
    if has_any(text, ("non", "pas ca", "tu te trompes", "c'est faux")):
        return "Merci de me corriger. 😊 Qu'est-ce que j'ai mal compris ? Je vais ajuster ma réponse."
    if len(words) <= 3:
        return f"J'ai compris ton message : « {raw[:120]} ». Tu peux ajouter un peu de contexte pour que je cerne mieux ce que tu veux ?"

    return (
        f"Si je comprends bien, tu me parles de : « {raw[:220]} ». "
        "Je ne veux pas faire semblant de tout savoir : sans modèle IA externe, mon cerveau local reste limité. "
        "Précise le résultat que tu attends, et je chercherai la meilleure réponse parmi mes capacités actuelles."
    )

async def generate_reply(prompt: str, key: tuple) -> str:
    history = histories[key]
    if CHATBOT_API_URL and CHATBOT_MODEL and CHATBOT_API_KEY:
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
                        details = (await response.text())[:300]
                        log.warning("Endpoint NOVA HTTP %s: %s", response.status, details)
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, IndexError, TypeError, ValueError):
            log.warning("Endpoint NOVA indisponible, réponse locale utilisée.", exc_info=True)

    answer = local_reply(prompt, history)
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

    # Même message reçu deux fois : une seule réponse au maximum.
    if message.id in processed_message_id_set:
        return
    if len(processed_message_ids) == processed_message_ids.maxlen:
        expired_id = processed_message_ids[0]
        processed_message_id_set.discard(expired_id)
    processed_message_ids.append(message.id)
    processed_message_id_set.add(message.id)

    content = message.content or ""
    mentions_bot = client.user is not None and client.user in message.mentions
    called_nova = re.search(r"(?<!\w)nova(?!\w)", content, flags=re.IGNORECASE) is not None
    if not (mentions_bot or called_nova):
        return

    # Un seul message de réponse par membre toutes les 5 secondes.
    now = asyncio.get_running_loop().time()
    cooldown_key = (message.guild.id, message.author.id)
    if now - last_reply_at.get(cooldown_key, 0) < 5:
        return
    # Réserve le créneau avant le premier await pour éviter les réponses concurrentes.
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
        await message.reply(answer[:1800], mention_author=False, allowed_mentions=discord.AllowedMentions.none())
    except discord.DiscordException:
        log.exception("Impossible d'envoyer la réponse de NOVA")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("La variable DISCORD_TOKEN est absente. Ajoute-la dans les variables d'environnement de Render.")
    client.run(DISCORD_TOKEN, log_handler=None)
