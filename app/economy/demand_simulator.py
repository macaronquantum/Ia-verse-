from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SyntheticDemandConfig:
    users: int = 100
    intensity: float = 1.0
    seasonality: float = 0.2


class DemandSimulator:
    def __init__(self, cfg: SyntheticDemandConfig) -> None:
        self.cfg = cfg

    def generate_revenue(self, base_price: float, tick: int) -> float:
        seasonal = 1 + self.cfg.seasonality * (1 if tick % 2 == 0 else -1)
        requests = self.cfg.users * self.cfg.intensity * seasonal
        return max(0.0, requests * base_price * 0.01)
