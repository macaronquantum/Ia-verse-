from __future__ import annotations

from app.business.startup_evolution import StartupState


class BusinessEngine:
    def transition(self, startup: StartupState, kpi_growth: float) -> str:
        if kpi_growth > 0.1:
            return startup.advance()
        return startup.stage
