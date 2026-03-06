# IA-Verse Backend (jeu économique virtuel + Autonomous Agent System v1)

Ce dépôt contient un backend de simulation économique enrichi avec un **Autonomous Agent System v1** compatible avec l'architecture existante (API Gateway v10, registre d'outils, marketplace, facturation énergie, exécution sandbox, connecteurs).

## Fonctionnalités principales

- Monde virtuel et ressources globales (`energy`, `food`, `metal`, `knowledge`).
- Agents et entreprises simulés par ticks.
- Banque: comptes, dépôts/retraits, prêts, remboursement, intérêts.
- Économie et production d'entreprises.
- API REST FastAPI.

## Nouveautés Autonomous Agent System v1

### 1) Module `app/agents/`

- `brain.py`: boucle cognitive globale.
- `planner.py`: décomposition de goals en tâches.
- `executor.py`: exécution des tâches via API Gateway v10 et outils.
- `goal_system.py`: goals persistants (priorité, deadline, reward).
- `tool_selector.py`: découverte/sélection d'outils (coût énergie, temps, réputation, taux de succès).
- `memory_manager.py`: mémoire short-term / long-term vector / episodic.
- `tool_factory.py`: pipeline de création d'outil (lint, scan sécurité, test sandbox).
- `business_builder.py`: création autonome de business (services/API/content/design/analytics).
- `agent_network.py`: communication inter-agents (delegation/discovery/negociation).
- `scheduler.py`: scheduler autonome (compatible workers Redis/Celery).
- `agent_loop.py`: loop autonome continue.

### 2) Tables persistantes (niveau world)

- `agents_table`
- `agent_goals`
- `agent_tasks`
- `agent_memory`
- `agent_transactions`

### 3) Économie agent

- `agent_revenue`
- `agent_expenses`
- `tool_revenue`
- `marketplace_transactions`

### 4) Startup autonome

Au démarrage:
1. initialisation d'un monde bootstrap
2. création d'agents initiaux
3. chargement des outils marketplace
4. initialisation du système autonome
5. exécution via scheduler de fond

## Endpoints principaux

- `GET /health`
- `POST /worlds`
- `GET /worlds/{world_id}`
- `POST /worlds/{world_id}/agents`
- `POST /worlds/{world_id}/companies`
- `POST /worlds/{world_id}/tick`
- `POST /worlds/{world_id}/bank/deposit`
- `POST /worlds/{world_id}/bank/withdraw`
- `POST /worlds/{world_id}/bank/loan`
- `POST /worlds/{world_id}/bank/repay`
- `POST /worlds/{world_id}/autonomous/run`
- `GET /worlds/{world_id}/metrics`

## Lancer

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
python -m pytest -q
```
