# IA-Verse Backend

Backend de simulation multi-agents économique (off-chain temps réel + settlement on-chain quotidien du token **Core Energy** sur **Solana** via gateway stub).

## Architecture (haut niveau)

```text
Agents -> Strategy Manager -> Economy/Markets -> Reputation/Justice/Audit
   |            |                   |                 |
   v            v                   v                 v
Memory      Organizations      Production        API Gateway (wallet/external tools)
   \______________ Off-chain simulation engine (tick 5s, adaptive scheduler) ________/
                                |
                                v
                       Daily CoreEnergy settlement (on-chain hook)
```

## Modules clés

- `app/agents/strategies.py`: catalogue de stratégies persistantes + logique de switch (survie > pouvoir > sens).
- `app/economy/reputation.py`: score de réputation (transactions, défauts, jugements, contributions) + impact crédit/prix.
- `app/organizations/system.py`: lifecycle orgs (company/guild/state), IPO et secondaire via order book.
- `app/economy/markets.py`: limit/market orders, matching, fees, slippage, stub AMM.
- `app/agents/subagent_manifest.py`: manifest JSON auto pour sous-agents + tests simulés avant activation.
- `app/oracles/api_oracle.py`: `MintOracleAgent` unique + pipeline de preuve de valeur réelle (stub audit-safe).
- `app/justice/system.py`: Judge principal unique, sous-juges, gel, amendes (burn), ban et logs tamper-evident.
- `app/api_gateway/gateway.py`: accès monde réel via outils contrôlés (`create_wallet`, `place_order_on_exchange`, `call_external_api`, `run_job`).

## Coûts Core Energy (defaults)

Paramétrables dans `app/energy/core.py` :

- tick local reasoning: `0.01`
- external LLM call: base provider (`OpenAI`, `Anthropic`, `Google`) + scaling tokens/modèle
- create citizen: `0.2`
- create bank: `200`
- create state: `2000`
- spawn sub-judge: `75`

## Lancer en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Puis :
- API principale: `http://127.0.0.1:8000`
- Monitoring: `/monitoring/health`, `/monitoring/metrics`

## Tests

```bash
python -m pytest -q
```

## Checklist sécurité / privacy

- [x] Les agents n’accèdent pas directement à Internet (gateway obligatoire)
- [x] Quotas/permissions gateway appliqués
- [x] Mint lié à preuve vérifiable (stub), pas de branchement argent réel direct
- [x] Rôles uniques: 1 MintOracle, 1 Judge principal
- [x] Logs justice tamper-evident (chaînage hash)
- [x] Coûts énergétiques explicites et configurables
- [x] Settlement quotidien batché prêt pour hook on-chain Solana
- [x] Tests unitaires des comportements critiques/adverses (spawn/état coûteux, fake proof, unicité institutionnelle)
