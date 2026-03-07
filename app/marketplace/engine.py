"""Marketplace monetization helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RevenueSplit:
    creator: float
    platform: float
    affiliate: float


def compute_revenue_split(amount: float, platform_fee: float = 0.1, affiliate_fee: float = 0.0) -> RevenueSplit:
    platform = amount * platform_fee
    affiliate = amount * affiliate_fee
    creator = amount - platform - affiliate
    return RevenueSplit(creator=creator, platform=platform, affiliate=affiliate)
