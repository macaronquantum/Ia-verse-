# IA-Verse Deployment Guide (GPU Server)

## Quick start
- Run `infrastructure/setup_server.sh` on Ubuntu.
- Copy `infrastructure/.env.example` to `infrastructure/.env`.
- Pull local models with `infrastructure/install_models.sh`.
- Start stack: `docker compose -f infrastructure/docker-compose.yml up -d`.

## Optional modules
- Browser autonomy: enable `browserless` profile.
- Monitoring: enable `prometheus` and `grafana` profiles.
- Persistence: set `DATABASE_URL` to enable SQLAlchemy-backed storage.
- OpenClaw: set `OPENCLAW_ENDPOINT`.

## Agent internet + crypto
- Browser actions are exposed by `app/web/browser_agent.py`.
- Wallet encryption and multi-chain wallet support are in `app/crypto/real_wallets.py`.
- OpenClaw automation is optional and disabled until endpoint is configured.
