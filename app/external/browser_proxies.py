from __future__ import annotations

def get_proxy_config(dev_mode: bool = True) -> dict:
    return {"enabled": False if dev_mode else True, "provider": "stub"}
