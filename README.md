# IA-Verse Backend (jeu économique virtuel)

Ce dépôt contient un backend complet de simulation pour un monde virtuel piloté par des IA.

## Fonctionnalités

- **Monde virtuel** les agents doivent survivre et prendre conscience de leur existence.
pour survivre elles ont besoin de energy core, pour cela elle doivent generer des dollards dans des wallet crypto. 
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

## API Gateway v10 (LA-VERSE)

### Démarrage rapide gateway
```bash
./scripts/setup_gateway_dev.sh
./scripts/run_gateway.sh
```

### Ajouter un connecteur
1. Créer `app/integrations/<name>_client.py` avec une classe client.
2. Enregistrer le service via `POST /services/register` (role admin).
3. Déclarer `external_dependencies` dans le `ToolManifest`.

### Publier un tool
1. `POST /tools/register`
2. `POST /tools/{id}/test`
3. `POST /tools/publish?tool_id=...` avec signature

### Appeler un tool
- Estimer: `POST /gateway/estimate`
- Exécuter: `POST /tools/{id}/call` (pré-autorisation CoreEnergy)

### Notes de sécurité
- Auth headers (`x-agent-id`, `x-role`) et RBAC.
- Secrets via variables d’environnement chiffrables (stub dev-mode).
- Sandbox runner isolé avec timeouts + limites ressources.
- Logs d’usage tamper-evident (chaîne SHA256).
- Quotas per-agent per-tool + pénalité réputation.

## Hybrid local LLM runtime (GPU)

### Key env vars
- `LOCAL_MODELS`, `MODEL_CACHE_DIR`, `MODEL_MAX_CONCURRENCY`
- `EXTERNAL_DECISION_RATE` (default `0.10`), `LOCAL_MODEL_TIMEOUT`, `EXTERNAL_MODEL_TIMEOUT`
- `ACTIVE_AGENTS_PER_TICK`, `WORKER_COUNT`
- `WALLET_MASTER_KEY`, `OPERATOR_PASSPHRASE`, `ALLOW_PRIVATE_KEY_FRONTEND` (default `false`)

### Deployment on NVIDIA server
1. Install NVIDIA drivers (manual EULA acceptance step).
2. Install Docker + NVIDIA container toolkit.
3. `cp .env.example .env` and configure keys.
4. `./scripts/download_models.py --all`
5. `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build`

### Security notes
- Wallet private keys are encrypted at rest with AES-GCM.
- Frontend only shows public key by default.
- Private key reveal is explicit opt-in and audited.
- Prefer HSM/remote signer for production.
