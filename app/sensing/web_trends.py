from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List


@dataclass
class NormalizedEvent:
    source: str
    timestamp: str
    topic_tags: List[str]
    sentiment: float
    urgency: float
    metadata: Dict = field(default_factory=dict)


class SensingBus:
    """Simple in-memory Redis-like pub/sub bus for DEV_MODE tests."""

    def __init__(self) -> None:
        self._subscribers: List[Callable[[Dict], None]] = []
        self.events: List[Dict] = []

    def publish(self, event: NormalizedEvent) -> None:
        payload = asdict(event)
        self.events.append(payload)
        for callback in self._subscribers:
            callback(payload)

    def subscribe(self, callback: Callable[[Dict], None]) -> None:
        self._subscribers.append(callback)


def make_event(source: str, topic_tags: List[str], sentiment: float, urgency: float, metadata: Dict) -> NormalizedEvent:
    return NormalizedEvent(
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        topic_tags=topic_tags,
        sentiment=sentiment,
        urgency=urgency,
        metadata=metadata,
    )
