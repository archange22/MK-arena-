# NOVA v0.1.3

## Ce qui a changé

- détection NOVA plus stricte et plus fiable ;
- contexte conversationnel plus utile pour les demandes courtes ;
- meilleure logique d'indexation des informations de tournois ;
- mémoire de tournoi plus structurée ;
- permissions staff appliquées à travers des vérifications de sécurité ;
- commandes `/nova-status` et `/nova-sync` conservées et stabilisées ;
- architecture préparée pour les prochaines évolutions sans dépendre d'une API externe.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Tests

```bash
pytest -q
```

## Limite de la version

Cette version reste une base modulaire, locale, stable et extensible. Elle n'ajoute pas de grand modèle de langage ni de dépendance cloud.
