# NOVA v0.2

## Objectif

La v0.2 vise à rendre NOVA plus naturelle, plus utile et plus fiable dans les conversations Discord réelles.

## Nouvelles améliorations

- meilleure compréhension des formulations variées ;
- contexte conversationnel plus robuste ;
- mémoire conversationnelle plus propre ;
- gestion du message référencé (`reply` / contexte précédent) ;
- tournois mieux identifiés et mieux recherchés ;
- permissions staff vérifiées par des contrôles explicites ;
- architecture prête pour des évolutions sans dépendre d'une API externe.

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

## Limite de cette version

La v0.2 reste locale et modulaire. Elle n'ajoute pas encore de grand modèle de langage externe ni d'auto-apprentissage non supervisé.
