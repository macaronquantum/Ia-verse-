# GPU deployment runbook

Manual steps are required for NVIDIA driver installation and model license acceptance.

```bash
./scripts/setup_server.sh
```

Troubleshooting:
- `nvidia-smi` should list GPU.
- `docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi`
