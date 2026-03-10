from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List
from urllib.parse import urlparse

from app.sensing.web_trends import SensingBus, make_event


@dataclass
class CrawlPolicy:
    per_domain_limit: int = 2
    allowed_domains: List[str] | None = None


class WebCrawler:
    """Polite local crawler stub (no outbound network in tests)."""

    def __init__(self, bus: SensingBus, policy: CrawlPolicy | None = None) -> None:
        self.bus = bus
        self.policy = policy or CrawlPolicy()
        self._domain_counts: Dict[str, int] = {}

    def crawl(self, pages: Iterable[Dict[str, str]]) -> List[Dict]:
        extracted: List[Dict] = []
        for page in pages:
            url = page["url"]
            domain = urlparse(url).netloc
            if self.policy.allowed_domains and domain not in self.policy.allowed_domains:
                continue
            if self._domain_counts.get(domain, 0) >= self.policy.per_domain_limit:
                continue
            self._domain_counts[domain] = self._domain_counts.get(domain, 0) + 1
            text = page.get("html", "").lower()
            tags = [k for k in ["launch", "repo", "trend", "funding"] if k in text]
            if tags:
                evt = make_event("web_crawler", tags, sentiment=0.2, urgency=0.7, metadata={"url": url})
                self.bus.publish(evt)
                extracted.append(self.bus.events[-1])
        return extracted
