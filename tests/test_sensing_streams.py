from app.business.opportunity_engine import OpportunityEngine
from app.sensing.finance_stream import FinanceStream
from app.sensing.twitter_stream import TwitterStream
from app.sensing.web_trends import SensingBus


def test_sensing_streams_publish_normalized_events() -> None:
    bus = SensingBus()
    opp = OpportunityEngine()
    bus.subscribe(opp.on_event)

    evt1 = TwitterStream(bus).ingest(["ai", "launch"], sentiment=0.8, urgency=0.9)
    evt2 = FinanceStream(bus).ingest_quote("LAV", 10.5)

    assert evt1["source"] == "twitter"
    assert evt2["metadata"]["symbol"] == "LAV"
    assert len(opp.opportunities) == 2
