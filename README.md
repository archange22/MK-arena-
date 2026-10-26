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

## Déploiement et configuration sur Render

- **Dashboard Render :** https://dashboard.render.com/
- **Dépôt GitHub :** https://github.com/archange22/MK-arena-

Le fichier `render.yaml` configure un **Background Worker** Python.

1. Ouvre le [dashboard Render](https://dashboard.render.com/) et sélectionne le service de NOVA. Si aucun service n'existe, crée un service à partir du Blueprint `render.yaml` ou crée un Background Worker depuis ce dépôt.
2. Ouvre l'onglet **Environment** du service.
3. Ajoute `DISCORD_TOKEN), qui contient le token privé du bot.
4. Pour activer la mémoire persistante, ajoute aussi les variables Supabase indiquées dans la section suivante.
5. Enregistre les changements, laisse Render redémarrer/redéployer le service, puis vérifie les logs pour confirmer que le bot démarre correctement.

Ne jamais committer le token Discord dans GitHub.

## Mémoire persistante de NOVA avec Supabase

Le projet Supabase dédié est `mk-arena` (région `eu-west-1`). La table `public.mk_nova_conversations` conserve le fil partagé de chaque salon : seuls les 30 derniers messages du fil sont conservés, et la mémoire peut être rechargée après un redémarrage.

Dans **Render > service NOVA > Environment**, configure ces variables :

- **Nom :** `SUPABASE_URL`  
  **Valeur :** `https://nkhfaptkrenxtogellhv.supabase.co`
- **Nom :** `SUPABASE_SECRET_KEY`  
  **Valeur :** une clé **Secret** de ce projet, à récupérer dans [Supabase > API Keys](https://supabase.com/dashboard/project/nkhfaptkrenxtogellhv/settings/api-keys).

La variable `SUPABASE_SERVICE_ROLE_KEY` est aussi acceptée à la place de `SUPABASE_SECRET_KEY` pour les anciens projets. N'utilise jamais une clé Secret ou service-role dans le code source, dans GitHub ou dans une application publique. Ne partage pas cette clé dans le chat. Elle doit rester dans les variables privées du service Render.

La mémoire est organisée par serveur et salon Discord. NOVA ne sauvegarde que les messages auxquels le bot répond, pas tous les messages du salon. Informe les membres que les échanges adressés à NOVA sont conservés dans Supabase.

Sans clé Supabase dans Render, NOVA continue de fonctionner avec une mémoire temporaire en RAM. L'ajout des variables ne confirme pas à lui seul que tout fonctionne : vérifie les logs Render après le redémarrage.

## Développement local

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Configurer la variable d'environnement `DISCORD_TOKEN`, puis lancer :

```bash
python main.py
```
