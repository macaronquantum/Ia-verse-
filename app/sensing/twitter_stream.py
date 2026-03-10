from __future__ import annotations
from app.sensing.web_trends import SensingBus, make_event

class TwitterStream:
    source_name = "twitter"
    def __init__(self, bus: SensingBus) -> None:
        self.bus=bus
    def ingest(self, topic_tags, sentiment=0.0, urgency=0.5, metadata=None):
        e=make_event(self.source_name, topic_tags, sentiment, urgency, metadata or {})
        self.bus.publish(e)
        return self.bus.events[-1]
