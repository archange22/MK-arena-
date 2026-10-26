import os
import logging
import re
import asyncio
import random
import difflib
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

# Historique partagé par salon : NOVA suit une conversation même si un autre membre intervient.
# Chaque entrée utilisateur est étiquetée avec le nom Discord de son auteur.
histories = defaultdict(lambda: deque(maxlen=30))
last_reply_at = {}
# Anti-doublon : empêche de traiter deux fois le même message Discord.
processed_message_ids = deque(maxlen=5000)
processed_message_id_set = set()

SYSTEM_PROMPT = (
    "Tu es NOVA, un chatbot francophone amical pour une communauté Discord. "
    "Discute naturellement avec les membres sur des sujets variés. "
    "Tu n'es pas un expert des tournois et tu ne prétends pas gérer le serveur. "
    "Tu ne peux pas exécuter de commandes, modérer des membres ni changer les réglages. "
    "Si tu ne connais pas une information, dis-le clairement et ne l'invente jamais. "
    "Donne des réponses plus développées et vraiment utiles : en général 3 à 6 phrases, "
    "avec une explication, un exemple concret ou des étapes lorsque cela aide. "
    "Pour les questions complexes, organise la réponse avec de petits paragraphes ou des listes. "
    "Pour une question simple ou une salutation, reste naturel sans faire un long discours. "
    "Tiens compte de l'historique partagé du salon et distingue les membres grâce à leur nom. "
    "Si un message est ambigu, pose une seule question précise. "
    "Réponds en français naturel, chaleureux et facile à comprendre."
)


def normalize_text(value: str) -> str:
    """Normalise accents et quelques abréviations du français informel."""
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9\s']", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    slang = {"slt": "salut", "bjr": "bonjour", "bsr": "bonsoir", "cc": "coucou",
             "pk": "pourquoi", "pq": "pourquoi", "pcq": "parce que", "koi": "quoi",
             "chui": "je suis", "jsuis": "je suis", "tkt": "ne t inquiete pas",
             "thx": "merci", "ty": "merci", "ptdr": "mort de rire", "mdr": "mort de rire"}
    for short, expanded in slang.items():
        value = re.sub(r"(?<!\w)" + re.escape(short) + r"(?!\w)", expanded, value)
    return re.sub(r"\s+", " ", value).strip()


def has_any(text: str, phrases: tuple[str, ...]) -> bool:
    """Recherche les expressions entières et tolère quelques petites fautes."""
    targets = [normalize_text(phrase) for phrase in phrases]
    for phrase in targets:
        if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text):
            return True
    tokens = text.split()
    for phrase in targets:
        target = phrase.split()
        if not target or not all(len(word) >= 5 for word in target):
            continue
        for index in range(max(0, len(tokens) - len(target) + 1)):
            candidate = tokens[index:index + len(target)]
            if all(len(word) >= 5 for word in candidate):
                score = difflib.SequenceMatcher(None, " ".join(candidate), " ".join(target)).ratio()
                if score >= 0.86:
                    return True
    return False
def local_reply(message: str, history=None) -> str:
    """Moteur conversationnel local avec intentions, variantes et mémoire courte."""
    raw = re.sub(r"\s+", " ", message).strip()
    text = normalize_text(raw)
    words = set(text.split())
    history = list(history or [])

    def choose(options):
        return random.choice(options)

    def last_user_message():
        return next(
            (item.get("content", "") for item in reversed(history) if item.get("role") == "user"),
            "",
        )

    if not text:
        return choose([
            "Je t'écoute 😊 Tu voulais me demander quelque chose ?",
            "Je suis là ! Donne-moi un sujet et on en parle.",
            "À toi la parole 🤖 Qu'est-ce que tu as en tête ?",
        ])

    # Identité et capacités
    if has_any(text, ("qui es tu", "tu es qui", "c'est quoi nova", "ton nom", "presente toi", "qui est nova")):
        return "Je suis NOVA, le chatbot de MK Arena 🤖. Je peux discuter, proposer des idées et t'aider à réfléchir. Je fonctionne actuellement avec des règles locales, donc je peux encore mal comprendre certaines demandes."
    if has_any(text, ("que peux tu faire", "tu sais faire quoi", "aide moi", "comment tu fonctionnes", "tes capacites", "tu peux faire quoi")):
        return "Je peux discuter, aider à organiser une idée, parler de jeux, de Discord, de cours ou de programmation. Explique-moi ton objectif et je te dirai ce que je peux faire, sans prétendre avoir des capacités que je n'ai pas."

    # Salutations, humeur et politesse
    if has_any(text, ("bonjour", "salut", "hello", "bonsoir", "coucou", "yo", "wesh", "slt", "bjr", "cc")):
        return choose([
            "Salut ! 😊 Quoi de neuf ?",
            "Hey ! NOVA est là 🤖 On parle de quoi ?",
            "Yo 👋 Comment se passe ta journée ?",
            "Salut ! Balance ton sujet, je t'écoute.",
        ])
    if has_any(text, ("ca va", "comment vas tu", "comment tu vas", "tu vas bien", "la forme")):
        return choose([
            "Ça va bien côté NOVA 🤖 Merci ! Et toi, comment ça se passe ?",
            "Toujours opérationnelle 😊 Et toi, la forme ?",
            "Tout roule dans mes circuits ! Et de ton côté ?",
        ])
    if has_any(text, ("merci", "thanks", "bien joue", "bravo", "merci beaucoup", "thx", "ty")):
        return choose(["Avec plaisir ! 😊", "Pas de souci, je suis là pour ça.", "Content que ça t'aide ! 🤖", "Quand tu veux !"])
    if has_any(text, ("au revoir", "a plus", "bonne nuit", "a demain", "je dois partir", "bye", "bonne journee")):
        return choose(["À plus ! 👋", "Bonne continuation, on reprendra quand tu voudras.", "Prends soin de toi et à bientôt ! 👋"])

    # Questions sur NOVA et réactions à ses réponses
    if has_any(text, ("tu comprends", "tu comprends rien", "tu es bete", "tu es nul", "tu as rien compris", "t'as pas compris")):
        return "Possible que j'aie mal compris 😅 Dis-moi ce que tu voulais dire ou donne un exemple, et je vais essayer de corriger le tir."
    if has_any(text, ("repete", "redis", "qu'est ce que tu viens de dire", "tu as dit quoi", "repete stp")):
        previous = next((item.get("content", "") for item in reversed(history) if item.get("role") == "assistant"), "")
        return "Ma réponse précédente : " + previous[:900] if previous else "Je n'ai pas encore de réponse précédente à répéter ici."
    if has_any(text, ("tu es une ia", "tu es un robot", "tu es humain", "tu es humaine", "tu es reel")):
        return "Je suis un bot logiciel, pas une personne. 🤖 Pour le moment, je réponds grâce à des règles locales et, seulement si une clé API est configurée, à un modèle externe."

    # Petites conversations et soutien
    if has_any(text, ("blague", "fais moi rire", "raconte une blague", "une blague")):
        return choose([
            "Pourquoi les programmeurs confondent-ils Halloween et Noël ? Parce que OCT 31 = DEC 25. 🎃",
            "Pourquoi le développeur aime-t-il le noir ? Parce que la lumière attire les bugs. 🐛",
            "Un ordinateur entre dans un bar. Le barman dit : « Désolé, on ne sert pas les processeurs. » 🤖",
        ])
    if has_any(text, ("je m'ennuie", "ennuye", "je sais pas quoi faire", "rien a faire")):
        return "On peut trouver un truc sympa 😊 Tu préfères parler de jeux vidéo, inventer un projet, faire un quiz ou simplement discuter ?"
    if has_any(text, ("je suis triste", "pas le moral", "je vais mal", "je suis stresse", "je suis stressé", "je suis fatigue", "j'ai peur", "je suis inquiet")):
        return "Désolé que tu te sentes comme ça 💛 Si tu veux, raconte-moi ce qui se passe. Je peux t'écouter et t'aider à réfléchir à la prochaine petite étape."
    if has_any(text, ("je suis content", "je suis heureux", "bonne nouvelle", "j'ai reussi", "ça a marché", "ca a marche")):
        return choose(["Excellent ! 🎉 Raconte, qu'est-ce qui s'est passé ?", "Ça fait plaisir à lire 😊 Qu'est-ce qui a bien marché ?", "Bien joué ! Tu veux me raconter la suite ?"])

    # Demandes directes et questions courantes
    if has_any(text, ("oui", "exact", "c'est ca", "voila", "d'accord", "ok", "okay", "ouais", "yep")) and len(words) <= 4:
        return choose(["D'accord 😊 On continue.", "Ça marche ! Quelle est la suite ?", "Compris. Qu'est-ce que tu veux faire maintenant ?"])
    if has_any(text, ("non", "pas ca", "tu te trompes", "c'est faux", "non pas du tout")) and len(words) <= 7:
        return "Merci de me corriger. 😊 Dis-moi ce qui est faux ou ce que tu voulais dire, et je vais ajuster ma réponse."
    if has_any(text, ("pourquoi", "comment", "explique", "c'est quoi", "qu'est ce que", "definition", "ca veut dire", "signifie")):
        return (
            f"Ta question porte sur : « {raw[:180]} ». Je peux repérer le type de question, mais mon mode local ne connaît pas tous les sujets. "
            "Ajoute le contexte ou précise ce que tu veux savoir, et je ferai de mon mieux sans inventer de faits."
        )

    # Domaines connus : réponses plus ciblées
    if has_any(text, ("codm", "call of duty", "blood strike", "free fire", "jeu", "gaming", "game", "minecraft", "roblox", "fortnite", "football", "basket")):
        return choose([
            "On part sur le gaming 🎮 Tu veux parler de stratégie, de réglages, de progression ou d'un jeu précis ?",
            "Sujet jeux vidéo détecté 🎮 Dis-moi le jeu et ton objectif, et je t'aiderai à trouver une piste.",
            "Gaming time ! 🎮 Tu cherches des conseils, une idée de défi ou juste une discussion sur un jeu ?",
        ])
    if has_any(text, ("ecole", "devoir", "cours", "exercice", "revision", "examen", "math", "francais", "anglais", "histoire", "geographie", "physique", "chimie")):
        return "On s'y met 📚 Envoie l'énoncé ou précise la matière et ce que tu ne comprends pas. Je peux t'expliquer les étapes."
    if has_any(text, ("discord", "serveur", "salon", "role", "bot", "commande slash", "moderation")):
        return "Pour Discord, je peux t'aider à réfléchir à la structure d'un serveur, aux rôles ou au code d'un bot. Quel problème précis veux-tu régler ?"
    if has_any(text, ("site web", "application", "programmer", "code", "github", "developper", "developpement", "ia", "intelligence artificielle", "api", "python", "javascript", "html", "css")):
        return "On parle de création numérique 💻 Dis-moi ce que tu construis, le résultat attendu et, si tu as une erreur, copie son message exact."
    if has_any(text, ("ami", "amie", "amour", "dispute", "relation", "personne me parle", "je me sens seul")):
        return "Les relations peuvent être compliquées. 💛 Si tu veux, explique-moi la situation et ce que tu aimerais voir changer. On peut réfléchir à plusieurs options."

    # Continuité conversationnelle simple
    previous_user = last_user_message()
    if has_any(text, ("et toi", "et alors", "ensuite", "apres", "continue", "continue stp", "developpe", "explique plus")):
        last_assistant = next((item.get("content", "") for item in reversed(history) if item.get("role") == "assistant"), "")
        if last_assistant:
            return "Je développe 😊 Voici le point précédent : " + last_assistant[:650] + "\n\nQuelle partie veux-tu approfondir ?"
        return "Je peux continuer 😊 Donne-moi le sujet à développer."
    if text in ("hein", "quoi", "comment", "pourquoi", "explique", "vas y", "vazy"):
        last_assistant = next((item.get("content", "") for item in reversed(history) if item.get("role") == "assistant"), "")
        if last_assistant:
            return "Tu veux que je précise ma réponse précédente ? 😊 " + last_assistant[:500]
        return "Tu veux que je t’explique quoi exactement ? Donne-moi le sujet."
    if has_any(text, ("et ensuite", "et apres", "comment ca marche")) and previous_user:
        return f"Tu fais référence à « {previous_user[:160]} » ? Je peux expliquer la suite ou le fonctionnement. Tu préfères quoi ?"
    if len(words) <= 3:
        return choose([
            f"J'ai noté « {raw[:120]} ». Tu peux m'en dire un peu plus pour que je comprenne mieux ?",
            f"Tu parles de « {raw[:120]} » : tu veux une explication, un conseil ou juste en discuter ?",
            "Je t'écoute. Ajoute un peu de contexte et je pourrai mieux viser.",
        ])

    return (
        f"Si je comprends bien, tu veux parler de : « {raw[:220]} ». "
        "Je ne suis pas sûr d'avoir saisi l'objectif exact. Tu veux une explication, des conseils, une solution ou un avis ?"
    )

async def generate_reply(prompt: str, key: tuple) -> str:
    # La clé représente le salon, pas le membre : tous les participants partagent le même fil.
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
                        "max_tokens": 700,
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
    # Déclenchement insensible à la casse, quelle que soit la position dans le message.
    called_nova = re.search(r"nova", content, flags=re.IGNORECASE) is not None
    if not (mentions_bot or called_nova):
        return

    prompt = content
    if client.user:
        prompt = prompt.replace(f"<@{client.user.id}>", "").replace(f"<@!{client.user.id}>", "")
    # Retire toutes les variantes de NOVA du texte transmis au moteur local.
    prompt = re.sub(r"nova", "", prompt, flags=re.IGNORECASE)
    prompt = re.sub(r"\s+", " ", prompt).strip(" ,.!?\n\t")
    if not prompt:
        prompt = "Présente-toi brièvement et demande-moi de quoi je veux parler."

    try:
        async with message.channel.typing():
            speaker = message.author.display_name or message.author.name
            shared_prompt = f"{speaker}: {prompt}"
            answer = await generate_reply(shared_prompt, (message.guild.id, message.channel.id))
        await message.reply(answer[:1800], mention_author=False, allowed_mentions=discord.AllowedMentions.none())
    except discord.DiscordException:
        log.exception("Impossible d'envoyer la réponse de NOVA")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise RuntimeError("La variable DISCORD_TOKEN est absente. Ajoute-la dans les variables d'environnement de Render.")
    client.run(DISCORD_TOKEN, log_handler=None)
