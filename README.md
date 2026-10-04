# 🤖 NOVA v2.0 — Personal Autonomous AI & Coding Engine (MK ARENA)

## 🌟 Vision du Projet

**NOVA v2.0** transforme le bot Discord de MK ARENA en un véritable agent autonome capable de :
1. **Comprendre et converser naturellement** avec les utilisateurs Discord ou via API locale.
2. **Analyser, générer et modifier du code** de manière sécurisée grâce à une boucle fermée d'agentique.
3. **Tester ses modifications dans un bac à sable (Sandbox)** avec `pytest` avant toute application sur le dépôt principal.
4. **Auto-corriger ses erreurs** et proposer des améliorations contrôlées via un système de propositions (`proposals/`) et de branches Git.
5. **Adopter une personnalité dynamique** (Normal, Friendly, Serious, Annoyed et Sarcastic/GLaDOS) réagissant intelligemment aux provocations et pardonnant les excuses.

---

## 🏛️ Architecture Globale (v2.0)

```
NOVA v2.0
├── ai/
│   ├── engine.py              # Moteur unifié & parsing d'instructions
│   ├── code_agent.py          # Orchestrateur de missions de code
│   ├── planner.py             # Planificateur multi-étapes (OBSERVE -> PLAN -> ACT -> TEST -> DONE)
│   ├── reasoning.py          # Diagnostic d'échecs de tests & hypothèses de correction
│   ├── personality.py        # Moteur d'humeurs (Normal, GLaDOS, Annoyed, Friendly)
│   ├── context.py            # Mémoire conversationnelle à court terme
│   └── intent.py             # Détecteur d'intentions
│
├── coding/
│   ├── analyzer.py           # Analyseur AST du projet, modules, classes et fonctions
│   ├── validator.py          # Barrière de sécurité : fichiers protégés & motifs interdits
│   ├── editor.py             # Écriture atomique, patch de ligne & rollback automatique
│   ├── tester.py             # Exécuteur automatisé de pytest avec rapport d'erreurs
│   ├── sandbox.py            # Bac à sable temporaire pour tester les modifications
│   └── generator.py          # Générateur de fonctions, classes et tests unitaires
│
├── self_improvement/
│   ├── manager.py            # Chef d'orchestre de la boucle d'auto-amélioration
│   ├── proposals.py          # Registre des propositions d'amélioration (JSON)
│   ├── evaluator.py          # Métriques de santé, taux de succès et temps de réponse
│   └── history.py            # Journal d'audit de chaque version et modification
│
├── git_agent/
│   └── manager.py            # Wrapper Git automatique (branches, commits, rollback)
│
├── memory/
│   ├── database.py           # SQLite persistant
│   └── conversation.py       # Historique et rancunes par serveur
│
├── security/                 # Protection anti-raid, modération et permissions
├── tournaments/              # Gestion des tournois MK ARENA
└── tests/                    # Suite de 27 tests unitaires automatisés
```

---

## 🚀 Ce que NOVA sait faire (v2.0)

### 1. Agent de Programmation & Boucle d'Auto-Amélioration
- **Lecture et cartographie du code** : NOVA scanne l'intégralité du projet via AST (`CodeAnalyzer`), identifie les classes, fonctions et dépendances.
- **Protection & Sécurité stricte** : `CodeValidator` interdit formellement de toucher aux fichiers critiques (`security/`, `main.py`, `.env`) et bloque toute commande destructive (`rm -rf`, `eval`, injection).
- **Bac à sable (Sandbox)** : toute proposition de modification est clonée dans un espace isolé temporaire et testée avec `pytest`.
- **Raisonnement d'erreur** : en cas d'échec d'un test, `ReasoningEngine` analyse le traceback, identifie la ligne en cause et propose un correctif.
- **Historique & Traçabilité** : chaque amélioration validée reçoit un ID unique sous `proposals/` et est enregistrée dans l'historique d'audit.
- **Intégration Git** : création automatique de branches de fonctionnalités (`nova/improve-...`) et commits standardisés avec auteur NOVA.

### 2. Conversation Naturelle & Personnalité Dynamique
- Répond aux mentions `@NOVA` et aux messages formulés en langage naturel.
- Détecte le contexte et permet les questions courtes de suivi (*"Et la date ?"*, *"Tu peux détailler ?"*).
- **Mode GLaDOS** : riposte sarcastique en cas d'insulte répétée, avec suspension de courtoisie.
- **Pardon immédiat** : réinitialisation en mode courtois dès que l'utilisateur formule des excuses (*"Pardon Nova"*, *"Désolé"*).

### 3. Tournois & Modération MK ARENA
- Gestion des règles, formats d'équipes et annonces de tournois.
- Système anti-raid, logs d'avertissements et rôles administratifs.

---

## 📋 Ce qui reste à faire (Roadmap v2.5 → v5.0)

- [ ] **v2.5 — Agent & Outils Étendus** :
  - Support de connecteurs d'outils externes (webhooks, API REST, notifications Discord riches).
  - Planification de tâches asynchrones en arrière-plan.
- [ ] **v3.0 — Modèle Local (Local LLM Engine)** :
  - Intégration d'un connecteur pour modèle de langage local (Ollama / llama.cpp) sans dépendance obligatoire à une API cloud payante.
- [ ] **v3.5 — Auto-évaluation continue** :
  - Métriques d'usage des commandes, détection automatique de questions sans réponse pour enrichir la base de connaissances.
- [ ] **v4.0 — Missions Autonomes Complexes** :
  - Capacité à concevoir une fonctionnalité complète en 15+ étapes avec validation humaine intermédiaire par bouton Discord.
- [ ] **v4.5 — Dashboard Web & Code Studio** :
  - Interface web de monitoring, éditeur de code interactif et vue en direct des tests et propositions d'amélioration.
- [ ] **v5.0 — NOVA Personal AI Ultime** :
  - Fusion totale du moteur de raisonnement local, mémoire vectorielle long terme, personnalité multi-états et indépendance réseau complète.

---

## 🛠️ Installation & Démarrage

```bash
# 1. Cloner le dépôt
git clone https://github.com/archange22/MK-arena-.git
cd MK-arena-

# 2. Configurer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env

# 5. Lancer les tests unitaires
pytest -v

# 6. Démarrer NOVA
python main.py
```

---

## ⚡ Architecture Avancée v2.1 → v5.0 (Core & Multi-Interface)

Le projet a été restructuré selon la spécification modulaire complète :

```
nova/
├── core/               # Cerveau central (nova.py, lifecycle.py, config.py)
├── ai/                 # Moteur IA abstrait & local (local_engine.py, structured_output.py)
├── memory/             # Mémoire sémantique, utilisateur, serveur & décomposition (semantic.py, retrieval.py, forgetting.py)
├── personality/        # Moteur d'humeurs dynamiques, style & filtre d'insultes/excuses (mood.py, behavior.py, insults.py)
├── discord_bot/        # Support @NOVA, replies, mentions et embeds riches (replies.py, mentions.py, embeds.py)
├── tools/              # ToolManager sécurisé (filesystem, git, python, pytest, web, discord)
├── coding/             # Analyseur AST, éditeur, patcher & reviewer automatique de code (patcher.py, reviewer.py)
├── agent/              # Planificateur multi-étapes, exécuteur, supervisor & retry policies (task.py, executor.py)
├── self_improvement/   # Expérimentations A/B, métriques & propositions (experiments.py, evaluator.py)
├── git_manager/        # Isolation des tâches par branches Git, commits & rollback (repository.py, branches.py, rollback.py)
├── security/           # Politiques sandbox, détection de secrets & audit log (secrets.py, audit.py, sandbox_policy.py)
├── dashboard/          # API REST & WebSocket prêts pour le frontend Web / Firebase (dashboard/api/, dashboard/websocket/)
└── tests/              # 36 tests unitaires automatisés avec pytest (100% passés)
```

### 🌐 Dashboard API & WebSocket
Le backend expose désormais les points d'accès suivants pour le Dashboard et le Code Studio :
- `GET /api/status` : Statut en direct de NOVA, CPU, mémoire, uptime, modèle actif.
- `GET /api/metrics` : Taux de succès des tests, tâches complétées, latence moyenne.
- `GET /api/tasks` : Liste des missions en cours et complétées.
- `GET /api/logs` : Journal d'audit et logs temps réel.
- `WS /ws` : Broadcaster d'événements pour l'interface temps réel.
