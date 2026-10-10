# MK Arena • Bot Discord

Bot Discord de la communauté MK Arena, développé avec Python et discord.py. Toutes les commandes utilisent uniquement le préfixe `!`.

## Commandes

### Général
- `!ping` : vérifie la latence du bot.
- `!aide` : affiche la liste des commandes.
- `!serveur` : affiche les informations du serveur.
- `!userinfo [membre]` : affiche les informations d'un membre.
- `!avatar [membre]` : affiche l'avatar d'un membre.

### Modération
- `!clear 10` : supprime jusqu'à 10 messages.
- `!kick @membre raison` : expulse un membre.
- `!ban @membre raison` : bannit un membre.
- `!timeout @membre 10 raison` : met un membre en timeout pour 10 minutes.
- `!slowmode 5` : règle le mode lent à 5 secondes.
- `!lock` : verrouille le salon actuel.
- `!unlock` : déverrouille le salon actuel.

Les commandes de modération exigent les permissions Discord appropriées pour la personne qui les utilise et pour le bot.

## Déploiement sur Render

Le fichier `render.yaml` configure un **Background Worker** Python.

1. Ouvrir le tableau de bord Render et connecter ce dépôt GitHub.
2. Créer le service à partir du Blueprint (`render.yaml`) ou créer un Background Worker avec ce dépôt.
3. Ajouter la variable d'environnement `DISCORD_TOKEN`, qui contient le token privé du bot.
4. Lancer le déploiement et vérifier les logs.

Ne jamais committer le token Discord dans GitHub.

## Développement local

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Configurer la variable d'environnement `DISCORD_TOKEN`, puis lancer :

```bash
python main.py
```
