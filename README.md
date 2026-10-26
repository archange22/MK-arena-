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


## Base de données Supabase (préparée, sans déploiement)

SQLite reste le mode par défaut. Pour utiliser le projet Supabase dédié **MK Arena** :
1. Installer les dépendances avec `pip install -r requirements.txt`.
2. Définir `DATABASE_BACKEND=supabase` dans les variables du service.
3. Définir `SUPABASE_DB_URL` avec l'URI PostgreSQL du projet MK Arena dans les paramètres Database de Supabase. Utiliser l'URI du pooler si l'hébergeur le nécessite.
4. Garder cette URI secrète dans les variables du service, jamais dans GitHub ni côté client Discord.
5. Tester d'abord sur une copie de la base SQLite. Les anciennes données ne sont pas importées automatiquement.

Le bot utilise les tables `public.mk_*` créées par les migrations. RLS est activé sans accès client public ; le bot doit se connecter côté serveur avec l'URI PostgreSQL privée. SQLite reste le mode de repli tant que `DATABASE_BACKEND=supabase` n'est pas défini.

**Ce changement est dans une branche séparée. Il ne déploie pas le bot et ne configure pas Render automatiquement.**
