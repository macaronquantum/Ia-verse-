# Model ops

Download configured models:

```bash
./scripts/download_models.py --all
```

Single model:

```bash
./scripts/download_models.py --model mistral-7b --quant 4bit --cache-dir /var/models
```

Tune with:
- `MODEL_MAX_CONCURRENCY`
- `ACTIVE_AGENTS_PER_TICK`
- `WORKER_COUNT`
