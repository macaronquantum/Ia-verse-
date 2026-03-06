# LA-VERSE Bootstrap + Runner + Gateway

## Prérequis
- Python 3.11+
- Docker + Docker Compose
- tmux (recommandé sur macOS)

## Variables d'environnement
Copier `.env.example` vers `.env` puis adapter:
- `TICK_SECONDS=5`
- `CORE_ENERGY_SUPPLY=10000`
- `CORE_EXCHANGE_RATE=1000000`
- `SETTLEMENT_TIME=00:00`
- `MINT_PRIVATE_KEY=...`
- `DEV_ALLOW_MINT=false` (mettre `true` en local si besoin)
- `ALCHEMY_API_KEY=...`

## Bootstrap du monde
```bash
python scripts/world_bootstrap.py
```
Crée 5 banques centrales régionales + allocations CoreEnergy + agents initiaux.

## Lancer toute la stack
```bash
./scripts/run_all.sh
```
- Postgres + Redis via `docker-compose.dev.yml`
- FastAPI
- Worker simulation (`run_worker.py --tick-seconds 5`)

## Runner simple
```bash
./scripts/run_simulation.sh 5
```

## Settlement journalier
```bash
python scripts/settlement_daily.py
```
Produit un reçu JSON dans `receipts/`.

## Dashboard
- URL: `http://localhost:8000/dashboard`
- Monitoring API:
  - `/monitoring/health`
  - `/monitoring/metrics`
  - `/monitoring/top_agents`
  - `/monitoring/world_map`
  - `/monitoring/logs`
  - websocket `/monitoring/events`

## API Gateway (exemples)
- `POST /gateway/create_wallet`
- `POST /gateway/transfer_funds`
- `POST /gateway/place_order`
- `POST /gateway/call_third_party`
- `POST /gateway/request_llm`
- `POST /gateway/create_tool`

Tous les appels gateway appliquent quota + coût CoreEnergy et passent par un service registry (stubs inclus, Alchemy stub prêt à remplacer).

## Human jobs
Le pipeline `app/oracles/jobs.py` permet de poster des tâches humaines simulées (`post_human_job`) complétées après quelques ticks (`process_jobs_tick`).

## Tests
```bash
python -m pytest -q
```
