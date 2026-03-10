# IA-Verse Architecture Overview

The core simulation loop and economic engine remain unchanged. New production modules are optional extensions:

- **Config layer**: `app/config/settings.py` centralizes env/default configuration.
- **LLM runtime**: `app/llm/local_runtime.py` routes Ollama/vLLM local inference with fallback.
- **Web autonomy**: `app/web/browser_agent.py` adds structured browser actions.
- **Integrations**: `app/integrations/openclaw_client.py` + `open_crow.py` bridge OpenClaw workflows.
- **Data intelligence**: `app/data/market_intelligence.py` for finance/market signals.
- **Real wallets**: `app/crypto/real_wallets.py` adds encrypted key handling for Solana/Ethereum workflows.
- **Sandbox execution**: `app/sandbox/docker_executor.py` runs generated Python in isolated Docker.
- **Persistence**: `app/storage/database.py` provides optional PostgreSQL models.
- **Scale runtime**: `app/runtime/agent_scheduler.py` adds optional Ray parallelization.
- **Monitoring**: `app/monitoring/metrics.py` exports Prometheus metrics.
- **Tools ecosystem**: `app/tools/` includes modular callable tools.
- **Cloud deployer**: `app/cloud/deployer.py` supports deployment commands.
- **Security controls**: `app/security/permissions.py` adds audit + tool permission checks.

All modules are opt-in and preserve backward compatibility by defaulting to no-op/stub behavior when not configured.
