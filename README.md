# 🏆 Chacha Live • Bot Discord MK ARENA

Bot Discord officiel de **MK ARENA** pour la gestion de la communauté et des tournois CODM.

## 🚀 Fonctionnalités de base
- **Architecture modulaire et propre** sous `discord.py`.
- **Commandes Slash synchronisées** avec gestionnaire d'erreur global (plus de blocage 'réfléchit...').
- **Système de permissions clair** : accessible aux administrateurs, aux rôles de gestion serveur/rôles, et au créateur.
- **Support Render** avec serveur de santé HTTP intégré sur `$PORT`.
- **Intégration continue (CI)** via GitHub Actions.

## ⚙️ Configuration
Créer un fichier `.env` ou renseigner sur votre hébergeur :
```env
DISCORD_TOKEN=votre_token_discord
PORT=10000
```

## 🧪 Tests
```bash
pytest -v
```
