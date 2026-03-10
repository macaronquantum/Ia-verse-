# Infrastructure Deployment

1. `./setup_server.sh`
2. Copy `.env.example` to `.env` and fill keys.
3. `./install_models.sh`
4. `docker compose up -d`

Use `docker compose --profile web up -d browserless` to enable autonomous web runtime.
Use `docker compose --profile monitoring up -d prometheus grafana` for observability.
