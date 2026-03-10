from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from time import time
from typing import List


@dataclass
class TamperEvent:
    timestamp: float
    event_type: str
    payload: str
    prev_hash: str
    hash: str


class TamperEvidentLog:
    def __init__(self) -> None:
        self._events: List[TamperEvent] = []

    def append(self, event_type: str, payload: str) -> TamperEvent:
        prev = self._events[-1].hash if self._events else "GENESIS"
        stamp = time()
        digest = sha256(f"{stamp}|{event_type}|{payload}|{prev}".encode()).hexdigest()
        event = TamperEvent(stamp, event_type, payload, prev, digest)
        self._events.append(event)
        return event

    @property
    def events(self) -> List[TamperEvent]:
        return list(self._events)

    def verify(self) -> bool:
        prev = "GENESIS"
        for e in self._events:
            expected = sha256(f"{e.timestamp}|{e.event_type}|{e.payload}|{prev}".encode()).hexdigest()
            if expected != e.hash:
                return False
            prev = e.hash
        return True
