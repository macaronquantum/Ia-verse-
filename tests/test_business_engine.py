from app.business.engine import BusinessEngine
from app.economy.opportunity_engine import Opportunity


def test_generate_and_provision_business() -> None:
    engine = BusinessEngine()
    opp = Opportunity("1", "SaaS", "CRM helper", 10, 100, ["dev"], 0.2, 12)
    plan = engine.generate_plan(opp)
    business_id = engine.provision_business("agent-x", plan)
    assert business_id in engine.businesses
    assert engine.businesses[business_id]["status"] == "active"
