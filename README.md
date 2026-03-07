# IA-Verse Backend

Autonomous Internet Economic Ecosystem v2 for LA-VERSE simulation.

## New v2 capabilities
- Internet sensing layer with normalized event bus streams.
- Controlled internet account automation manager with policy checks and encrypted credential storage stubs.
- Human workforce system restricted to **physical-world tasks** with escrow and judge escalation.
- Startup lifecycle progression (Idea -> Unicorn) with valuation model.
- Agent team reproduction and salary management.
- Expanded market primitives (orderbook), central bank mint/burn with tamper-evident logs.
- Synthetic demand simulator.
- Monitoring endpoints and `/dashboard` UI.
- Solana-like settlement stub script.
- DEV_MODE connectors for local simulation while preserving production integration points.

## Safety constraints
- Agents must not perform direct external network calls; integration points route via API gateway abstractions.
- Production-bound generated code must run in sandboxed runners and pass static checks (integration hooks documented).
- High-value finance/hiring operations must escalate to Judge thresholds.
- Monetary/mint-burn/hire operations use hash-chained tamper-evident logging.
- Never use automation to violate platform policies, privacy, or law.

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Dashboard: `http://localhost:8000/dashboard`

## Tests
```bash
pytest -q
```
