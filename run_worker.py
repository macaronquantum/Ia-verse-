from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request

from app.oracles.jobs import process_jobs_tick


def _post_json(url: str, payload: dict) -> dict | None:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_simulation_running(api_base_url: str) -> None:
    control_url = f"{api_base_url.rstrip('/')}/api/simulation/control"
    try:
        start_response = _post_json(control_url, {"action": "start"})
        if start_response and start_response.get("status") == "running":
            return
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            return
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return

    try:
        created = _post_json(control_url, {"action": "create_world", "world_name": "Production World"})
        if created and created.get("status") == "ok":
            _post_json(control_url, {"action": "start"})
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tick-seconds", type=float, default=5)
    args = parser.parse_args()

    api_base_url = os.getenv("API_BASE_URL", "http://api:8000")
    while True:
        ensure_simulation_running(api_base_url)
        process_jobs_tick()
        time.sleep(args.tick_seconds)


if __name__ == "__main__":
    main()
