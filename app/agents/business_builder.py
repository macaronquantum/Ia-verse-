"""Build commercial offerings from tools and perform virtual sales."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import COSTS


@dataclass
class SaleResult:
    gross: float
    creator_share: float
    platform_share: float


class BusinessBuilder:
    def create_listing(self, tool_id: str, pricing_model: str) -> dict:
        return {"tool_id": tool_id, "pricing_model": pricing_model, "status": "listed"}

    def settle_sale(self, amount: float) -> SaleResult:
        platform_share = amount * COSTS.marketplace_platform_fee
        return SaleResult(gross=amount, creator_share=amount - platform_share, platform_share=platform_share)
