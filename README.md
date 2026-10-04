# NOVA v0.3

## Objectif

La v0.3 améliore la compréhension naturelle et la mémoire de NOVA pour mieux tenir compte du contexte réel des conversations Discord.

## Nouvelles améliorations

- normalisation plus robuste du français et des formulations Discord ;
- reconnaissance d'intention plus fiable ;
- amélioration de la détection de tournoi et des requêtes de type règle / prix / équipe / date ;
- contexte conversationnel avec TTL et résumé récent ;
- réponse plus naturelle quand un utilisateur répond à un message précédent ;
- système de mémoire structuré plus lisible dans SQLite ;
- commandes `/nova-status` et `/nova-sync` préparées pour la suite.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Lancement

```bash
python main.py
```

## Tests

```bash
pytest -q
```

## Limite de cette version

La v0.3 reste locale et modulaire. Elle n'introduit pas encore de vrai moteur IA de type LLM local complet, mais elle prépare bien le terrain pour la v0.4.
