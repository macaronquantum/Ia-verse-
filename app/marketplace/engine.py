from __future__ import annotations

class MarketplaceEngine:
    def list_security(self, symbol: str, shares: int) -> dict:
        return {"symbol": symbol, "shares": shares, "status": "listed"}
