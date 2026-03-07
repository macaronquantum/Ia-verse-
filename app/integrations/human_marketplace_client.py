from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HumanTaskListing:
    platform: str
    title: str
    location: str


class HumanMarketplaceClient:
    def publish(self, listing: HumanTaskListing) -> dict:
        return {"ok": True, "id": f"{listing.platform}-stub-job", "location": listing.location}
