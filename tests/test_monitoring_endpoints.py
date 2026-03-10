from pathlib import Path

from app.api.monitoring import prometheus_metrics, world_metrics


def test_monitoring_payloads_and_dashboard_assets() -> None:
    world = world_metrics()
    assert "agent_count" in world
    metrics = prometheus_metrics()
    assert "agent_count" in metrics
    assert Path("web/dashboard/index.html").exists()
