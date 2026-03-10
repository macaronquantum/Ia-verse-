from __future__ import annotations
from app.sensing.web_trends import SensingBus, make_event

class FinanceStream:
    source_name = "finance"
    def __init__(self, bus: SensingBus) -> None:
        self.bus=bus
    def ingest_quote(self, symbol: str, price: float):
        e=make_event(self.source_name,["quote",symbol],0.0,0.8,{"symbol":symbol,"price":price})
        self.bus.publish(e)
        return self.bus.events[-1]
