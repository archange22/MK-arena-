# MK Arena • Bot Discord

Bot Discord de la communauté MK Arena, développé avec Python et discord.py.

## Commandes incluses
- `/ping` : vérifie la latence du bot.
- `/aide` : affiche les commandes disponibles.
- `!ping` et `!aide` : versions préfixées de base.

## Déploiement sur Render
Le fichier `render.yaml` configure un **Background Worker** Python. Pour le déployer :

1. Ouvrir le tableau de bord Render et connecter ce dépôt GitHub.
2. Créer le service à partir du Blueprint (`render.yaml`) ou créer un Background Worker avec ce dépôt.
3. Ajouter les variables d'environnement :
   - `DISCORD_TOKEN` : token privé du bot Discord.
   - `GUILD_ID` : identifiant numérique du serveur Discord, pour synchroniser rapidement les commandes slash sur ce serveur.
4. Lancer le déploiement et vérifier les logs.

Ne jamais committer le token Discord dans GitHub. Si `GUILD_ID` n'est pas défini, les commandes sont synchronisées globalement et leur propagation peut prendre plus de temps.

## Développement local
Installer les dépendances :

```bash
pip install -r requirements.txt
```

Configurer `DISCORD_TOKEN` et, de préférence, `GUILD_ID` comme variables d'environnement, puis lancer :

```bash
python main.py
```
