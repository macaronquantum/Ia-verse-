# IA-Verse Backend (jeu économique virtuel)

Ce dépôt contient un backend complet de simulation pour un monde virtuel piloté par des IA.

## Fonctionnalités

- **Monde virtuel** avec ressources globales (`energy`, `food`, `metal`, `knowledge`).
- **Agents IA** qui prennent des décisions automatiquement à chaque tick.
- **Banque**:
  - ouverture de comptes pour agents et entreprises,
  - dépôts / retraits,
  - prêts,
  - remboursement des prêts,
  - intérêts appliqués périodiquement.
- **Entreprises**:
  - création,
  - achat de matières,
  - production de biens,
  - vente automatique sur un marché simplifié.
- **Moteur de simulation** par ticks (un tick = un cycle économique).
- **API REST FastAPI** pour manipuler le monde et lancer la simulation.

## Lancer le serveur

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Le serveur sera disponible sur `http://127.0.0.1:8000`.

## Endpoints principaux

- `POST /worlds` : créer un nouveau monde
- `GET /worlds/{world_id}` : état détaillé du monde
- `POST /worlds/{world_id}/agents` : créer un agent IA
- `POST /worlds/{world_id}/companies` : créer une entreprise
- `POST /worlds/{world_id}/tick` : exécuter N ticks de simulation
- `POST /worlds/{world_id}/bank/deposit` : dépôt
- `POST /worlds/{world_id}/bank/withdraw` : retrait
- `POST /worlds/{world_id}/bank/loan` : demander un prêt
- `POST /worlds/{world_id}/bank/repay` : rembourser un prêt

## Philosophie de simulation

Le système inclut une IA de décision simple et extensible:

- un agent sans entreprise essaie d'en créer une,
- sinon il travaille, produit, vend et gère ses liquidités,
- il peut demander un prêt si sa trésorerie est faible,
- les prêts produisent des intérêts à chaque tick.

L'architecture est pensée pour être enrichie (nouvelles ressources, fiscalité, contrats, diplomatie, etc.).

## Tests

```bash
python -m pytest -q
```
