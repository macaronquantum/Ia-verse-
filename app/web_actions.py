from __future__ import annotations

import logging
import time
try:
    import requests
except Exception:
    requests = None
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

WEB_ACTION_ENERGY_COST = 0.3
MAX_STORED_ACTIONS = 20


@dataclass
class WebActionResult:
    action_type: str
    url: str
    status: str
    data: dict
    tick: int
    timestamp: float = field(default_factory=time.time)


class WebActionEngine:
    def __init__(self) -> None:
        self._agent_actions: dict[str, list[WebActionResult]] = {}
        if requests is None:
            self._session = None
            return
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "IA-Verse-Agent/1.0 (Autonomous Economic Agent)"
        })

    def perform_action(self, agent_id: str, action_type: str, url: str, tick: int, params: dict = None) -> WebActionResult:
        result_data = {}
        status = "failed"

        if self._session is None:
            return WebActionResult(action_type=action_type, url=url[:200], status="failed", data={"error": "requests dependency unavailable"}, tick=tick)

        try:
            if action_type == "fetch_data":
                resp = self._session.get(url, timeout=10, params=params)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if "json" in content_type:
                    result_data = {"content": resp.json(), "status_code": resp.status_code}
                else:
                    result_data = {"content": resp.text[:2000], "status_code": resp.status_code}
                status = "success"

            elif action_type == "check_service":
                resp = self._session.head(url, timeout=5)
                result_data = {
                    "status_code": resp.status_code,
                    "available": resp.status_code < 400,
                    "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
                }
                status = "success"

            elif action_type == "api_call":
                method = (params or {}).pop("method", "GET")
                if method.upper() == "GET":
                    resp = self._session.get(url, timeout=10, params=params)
                else:
                    resp = self._session.post(url, timeout=10, json=params)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if "json" in content_type:
                    result_data = {"response": resp.json(), "status_code": resp.status_code}
                else:
                    result_data = {"response": resp.text[:2000], "status_code": resp.status_code}
                status = "success"

            elif action_type == "market_data":
                api_url = "https://api.coingecko.com/api/v3/simple/price"
                coins = (params or {}).get("coins", "solana,bitcoin,ethereum")
                resp = self._session.get(api_url, params={"ids": coins, "vs_currencies": "usd", "include_24hr_change": "true"}, timeout=10)
                resp.raise_for_status()
                result_data = {"prices": resp.json()}
                status = "success"

            else:
                result_data = {"error": f"Unknown action type: {action_type}"}

        except requests.Timeout:
            result_data = {"error": "Request timed out"}
        except requests.RequestException as e:
            result_data = {"error": str(e)[:200]}
        except Exception as e:
            result_data = {"error": str(e)[:200]}

        action_result = WebActionResult(
            action_type=action_type,
            url=url[:200],
            status=status,
            data=result_data,
            tick=tick,
        )

        if agent_id not in self._agent_actions:
            self._agent_actions[agent_id] = []
        self._agent_actions[agent_id].append(action_result)
        if len(self._agent_actions[agent_id]) > MAX_STORED_ACTIONS:
            self._agent_actions[agent_id] = self._agent_actions[agent_id][-MAX_STORED_ACTIONS:]

        return action_result

    def get_agent_action_history(self, agent_id: str) -> list[dict]:
        actions = self._agent_actions.get(agent_id, [])
        return [
            {
                "action_type": a.action_type,
                "url": a.url,
                "status": a.status,
                "data_summary": str(a.data)[:300],
                "tick": a.tick,
                "timestamp": a.timestamp,
            }
            for a in actions
        ]

    def get_agent_knowledge(self, agent_id: str, max_recent: int = 3) -> str:
        actions = self._agent_actions.get(agent_id, [])
        if not actions:
            return ""
        recent = [a for a in actions[-max_recent:] if a.status == "success"]
        if not recent:
            return ""
        lines = ["Recent web action results:"]
        for a in recent:
            data_str = str(a.data)[:200]
            lines.append(f"  [{a.action_type}] {a.url[:60]} → {data_str}")
        return "\n".join(lines)
