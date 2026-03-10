from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SEARCH_ENERGY_COST = 0.5
MAX_RESULTS = 5
SEARCH_COOLDOWN_TICKS = 2
MAX_STORED_RESULTS = 10


@dataclass
class SearchResult:
    query: str
    results: list[dict]
    tick: int
    timestamp: float = field(default_factory=time.time)

    def summary(self, max_results: int = 3) -> str:
        lines = [f'Search: "{self.query}" (tick {self.tick})']
        for r in self.results[:max_results]:
            title = r.get("title", "")
            snippet = r.get("body", r.get("snippet", ""))
            if title:
                lines.append(f"  - {title}: {snippet[:150]}")
        return "\n".join(lines)


class WebSearchEngine:
    def __init__(self) -> None:
        self._agent_results: dict[str, list[SearchResult]] = {}
        self._agent_last_search_tick: dict[str, int] = {}
        self._ddgs = None

    def _get_ddgs(self):
        if self._ddgs is None:
            try:
                from ddgs import DDGS
                self._ddgs = DDGS()
            except ImportError:
                try:
                    from duckduckgo_search import DDGS
                    self._ddgs = DDGS()
                except Exception as e:
                    logger.warning(f"Failed to init DuckDuckGo search: {e}")
            except Exception as e:
                logger.warning(f"Failed to init DDGS: {e}")
        return self._ddgs

    def can_search(self, agent_id: str, current_tick: int) -> bool:
        last = self._agent_last_search_tick.get(agent_id, -999)
        return (current_tick - last) >= SEARCH_COOLDOWN_TICKS

    def search(self, agent_id: str, query: str, tick: int) -> SearchResult | None:
        ddgs = self._get_ddgs()
        if ddgs is None:
            return None

        try:
            raw_results = list(ddgs.text(query, max_results=MAX_RESULTS))
            results = []
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "url": r.get("href", r.get("link", "")),
                })
        except Exception as e:
            logger.warning(f"Web search failed for '{query}': {e}")
            results = [{"title": "Search unavailable", "body": str(e), "url": ""}]

        sr = SearchResult(query=query, results=results, tick=tick)
        self._agent_last_search_tick[agent_id] = tick

        if agent_id not in self._agent_results:
            self._agent_results[agent_id] = []
        self._agent_results[agent_id].append(sr)
        if len(self._agent_results[agent_id]) > MAX_STORED_RESULTS:
            self._agent_results[agent_id] = self._agent_results[agent_id][-MAX_STORED_RESULTS:]

        return sr

    def get_agent_knowledge(self, agent_id: str, max_recent: int = 3) -> str:
        results = self._agent_results.get(agent_id, [])
        if not results:
            return ""
        recent = results[-max_recent:]
        lines = ["Recent web research:"]
        for sr in recent:
            lines.append(sr.summary(max_results=2))
        return "\n".join(lines)

    def get_agent_search_history(self, agent_id: str) -> list[dict]:
        results = self._agent_results.get(agent_id, [])
        return [
            {
                "query": sr.query,
                "tick": sr.tick,
                "result_count": len(sr.results),
                "results": sr.results[:3],
                "timestamp": sr.timestamp,
            }
            for sr in results
        ]
