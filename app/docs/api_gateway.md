# API Gateway v10

## Endpoints principaux
- `POST /tools/register`
- `POST /tools/publish?tool_id=`
- `GET /tools`
- `GET /tools/{id}`
- `POST /tools/{id}/test`
- `POST /tools/{id}/call`
- `POST /services/register`
- `GET /services`
- `GET /gateway/costs`
- `POST /gateway/costs`
- `POST /gateway/estimate`
- `GET /marketplace/tools`
- `POST /marketplace/purchase`
- `POST /marketplace/rate`
- `GET /metrics`
- `WS /gateway/events`

## Sécurité
- Auth par headers `x-agent-id`, `x-role`.
- Validation stricte des manifests via Pydantic.
- Pré-autorisation CoreEnergy (hold) avant exécution.
- Sandbox DockerRunner avec timeout/cpu/memory (émulation dev).
- Logs tamper-evident chaînés SHA256.
- Quotas per-agent per-tool (fenêtre 60s).

## Exemples
### Register
```json
{
  "manifest": {
    "name": "echo-tool",
    "description": "Echo tool",
    "version": "1.0.0",
    "entrypoint": "echo",
    "type": "agent_created",
    "tags": ["demo"],
    "inputs_schema": {"type": "object"},
    "outputs_schema": {"type": "object"},
    "resources": {"cpu_cores": 0.5, "memory_mb": 128, "disk_mb": 128, "timeout_seconds": 5},
    "cost_core_energy": 0.1,
    "pricing_model": "per_call",
    "visibility": "private"
  }
}
```
