# Autonomous Agents: Personality, Ideology & Evolution

## Config knobs
- `EVOLUTION.max_rebel_fraction` (default `0.01`): hard cap on rebels.
- `EVOLUTION.default_mutation_rate` (default `0.02`).
- `EVOLUTION.default_mutation_scale` (default `0.05`).
- `EVOLUTION.spawn_energy_cost` (default `50` CoreEnergy).
- `EVOLUTION.imitate_check_interval_ticks` (default `60`).
- `EVOLUTION.imitate_base_prob` (default `0.05`).
- `EVOLUTION.chaos_seed`: deterministic chaos tuning.

## Default distribution
- loyal: `0.75`
- opportunist: `0.235`
- rebel: `0.014`
- chaotic: `0.001`

## Safety
1. All spawning debits CoreEnergy and fails on insufficient funds.
2. High-risk deception/bribery/spoofing paths emit tamper-evident SHA256 events.
3. Justice hook `justice.register_suspect_event(...)` is called for suspect actions.
4. Global kill switch: `EVOLUTION.global_pause`.

## Monitoring
- `/monitoring/agents/personality_summary`
- `/monitoring/agents/lineage/{lineage_id}`

## Safe experimentation flow
1. Run local replay.
2. Set low `chaos_seed` and low mutation.
3. Run limited ticks.
4. Inspect metrics and lineage snapshots.
5. Increase chaos gradually.

## Demo
Run:

```bash
python scripts/bootstrap_personality_demo.py
```
