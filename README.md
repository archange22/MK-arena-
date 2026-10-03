# NOVA v0.1

Première version fonctionnelle de l'IA Discord de MK ARENA.

## Fonctions

- Détection de `nova` sans tenir compte de la casse.
- Réponses générales de base.
- Contexte conversationnel récent.
- SQLite.
- Lecture/indexation de la catégorie TOURNOIS.
- Recherche des tournois et de leurs informations.
- Apprentissage explicite par le staff avec les guillemets.
- Permissions Discord pour les actions d'apprentissage.
- Commandes techniques `/nova-status` et `/nova-sync`.
- Architecture séparée entre Discord, mémoire, intentions et tournois.

## Installation

```bash
python -m venv .venv
# Linux/Termux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Renseigne `DISCORD_TOKEN` et `TOURNAMENT_CATEGORY_ID`.

## Permissions Discord

Le bot doit au minimum pouvoir voir les salons/messages nécessaires dans la catégorie des tournois et lire l'historique des messages. Pour les réponses, il doit pouvoir envoyer des messages.

Les intents `Guilds`, `GuildMessages` et `MessageContent` sont utilisés. Active **Message Content Intent** dans le Developer Portal Discord.

## Lancer

```bash
python main.py
```

## Apprentissage staff

Exemple:

`"nova retiens que le MK SQUID GAME compte 16 équipes et le prizepool est de 250 €."`

L'utilisateur doit avoir la permission `Manage Guild`, `Administrator`, ou être propriétaire du serveur.

## Important

Cette v0.1 n'est pas encore un grand modèle de langage local. Elle pose les fondations: mémoire, contexte, recherche, compréhension d'intentions et données de tournois. Le moteur IA est volontairement abstrait pour pouvoir être remplacé plus tard par un modèle local.
