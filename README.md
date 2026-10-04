# 🤖 NOVA v2.5 — Architecture Unifiée : DraftBot + GLaDOS + Coding Agent & Dashboard v2

> **NOVA** (Personal Artificial Intelligence) est un agent autonome unifié pour **MK ARENA | Events**, combinant les meilleures capacités d'un bot Discord complet (type DraftBot), une personnalité dynamique et sarcastique (type GLaDOS), un moteur de programmation auto-correcteur (Coding Agent) et un Dashboard Web professionnel temps réel prêt pour Firebase Hosting.

---

## 🏛️ Architecture Unifiée du Système

```
                    NOVA
                     │
        ┌────────────┼────────────┐
        │            │            │
     DISCORD      DASHBOARD     TERMINAL
        │            │            │
        └────────────┼────────────┘
                     │
                 NOVA CORE
                     │
      ┌──────────────┼──────────────┐
      │              │              │
    MEMORY         AGENT          TOOLS
      │              │              │
      │        ┌─────┼─────┐        │
      │      CODE  TESTS  GIT      │
      │                            │
      └────────── KNOWLEDGE ───────┘
```

---

## 🛡️ 1. Capacités Discord (Inspirées de DraftBot + GLaDOS)

### Modération & Sécurité
- **Commandes de modération** : `/ban`, bannissement temporaire, `/expulser`, `/avertir`, `/mute`, `/demute`, `/note`, historique des sanctions et journal d'audit.
- **Auto-modération** : Anti-spam, anti-liens frauduleux, anti-mentions excessives, anti-raid, contrôle des majuscules et suppression automatique configurée.
- **Accueil & Nouveaux membres** : Messages de bienvenue personnalisés, attribution automatique de rôles et salon de vérification.

### Communauté, Économie & Support
- **Niveaux & XP** : Progression d'expérience basée sur les messages réels, cartes de rangs et récompenses de rôles.
- **Économie virtuelle** : Pièces virtuelles, récompense quotidienne (`/daily`), boutique de rôles, inventaire et transferts sécurisés.
- **Support & Interaction** : Système de tickets avec transcripts, signalements anonymes pour le staff, boîte à suggestions avec votes et starboard (`#best-messages`).
- **Utilitaires** : Salons vocaux temporaires automatiques, rappels (`/rappel`), sauvegardes et messages automatiques planifiés.

### Gaming & Compétition (MK ARENA CODM)
- **Profils & Stats** : Suivi des statistiques Call of Duty Mobile (KD, matches, rangs, scrims).
- **Tournois MK ARENA** : Gestion des règles, formats (Search & Destroy, Hardpoint, etc.), recherche de tournois, inscriptions et classements d'équipes.

---

## 🤖 2. Personnalité Dynamique & Moteur GLaDOS

- **Mode Sarcasme & Évaluation** : Remarques acides et esprit acéré inspirés de GLaDOS lorsque sollicité ou provoqué.
- **Système de Rancune & Pardon** : Mémorisation des provocations utilisateur et retour au calme lors d'excuses explicites.
- **Changement de ton dynamique** : Détection du contexte et adaptation du niveau de formalisme selon les canaux (staff vs général).

---

## 🧑‍💻 3. Coding Agent & Boucle d'Auto-Amélioration

- **Analyse AST du code** : Cartographie continue de l'arbre syntaxique du projet (`coding/analyzer.py`).
- **Validation stricte des modifications** : Verrouillage des fichiers critiques (`.env`, `firebase.json`, `credentials.json`, `security/`) via `coding/validator.py`.
- **Sandbox & Rollback** : Toute proposition est exécutée dans un bac à sable temporaire avec tests `pytest` obligatoires avant commit.
- **Gestion Git automatisée** : Création de branches isolées (`nova/*`), calcul de diffs et registre des propositions (`proposals/`).

---

## 🌐 4. Dashboard Web v2 (Firebase Hosting & FastAPI)

- **Localisation** : `dashboard/public/index.html` (prêt pour `firebase deploy --only hosting`).
- **Backend API** : `backend/main.py` (FastAPI).
- **Zéro fausse donnée** : Affichage strict des métriques réelles du système, du dépôt Git et de la mémoire SQLite.
- **15 Centres de Contrôle** :
  1. Vue d'ensemble du Noyau IA & Métriques
  2. Chat unifié NOVA synchronisé avec Firebase Realtime Database
  3. Gestionnaire de mémoire SQLite hiérarchisée (Contextuel, Candidat, Validé)
  4. NOVA Lab (propositions d'apprentissage et validation humaine)
  5. Suivi des missions en direct
  6. Code Studio (explorateur de fichiers réels et visionneuse de code)
  7. Centre de tests avec exécution en direct de `pytest` (39 tests unitaires)
  8. Historique Git et gestion des branches
  9. Sécurité & Fichiers protégés
  10. Outils & Permissions
  11. Analytics & Télémétrie
  12. Modération & Auto-mod Discord
  13. Économie, Niveaux & Inventaire
  14. Tournois & Stats CODM
  15. Paramètres & Synchronisation Firebase

---

## 🧪 Tests & Qualité

La suite de tests automatisés comprend **39 tests unitaires** couvrant l'intégralité de l'architecture :
```bash
python -m pytest -v tests/
```

Tous les tests sont validés (100% passants).
