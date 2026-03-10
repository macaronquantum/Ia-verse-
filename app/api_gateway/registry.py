from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app.config import settings
from app.models.tool_manifest import ToolManifest, Visibility


@dataclass
class ToolVersion:
    id: str
    tool_id: str
    version: str
    manifest_json: dict[str, Any]
    status: str = "draft"


@dataclass
class UsageLog:
    id: str
    tool_id: str
    caller_agent_id: str
    status: str
    cost: float
    output: dict[str, Any] | None
    created_at: datetime
    hash: str


@dataclass
class Rating:
    tool_id: str
    agent_id: str
    score: int
    review: str


@dataclass
class Purchase:
    tool_id: str
    agent_id: str
    model: str
    amount: float


@dataclass
class ToolRecord:
    manifest: ToolManifest
    status: str = "draft"
    signature: str | None = None
    versions: list[ToolVersion] = field(default_factory=list)
    revenue: float = 0.0


class Registry:
    def __init__(self) -> None:
        self.tools: dict[str, ToolRecord] = {}
        self.services: dict[str, dict[str, Any]] = {}
        self.usage_logs: list[UsageLog] = []
        self.ratings: list[Rating] = []
        self.purchases: list[Purchase] = []
        self._chain_hash = "genesis"

    def register_tool(self, manifest_data: dict[str, Any]) -> ToolManifest:
        manifest = ToolManifest.model_validate(manifest_data)
        record = ToolRecord(manifest=manifest)
        version = ToolVersion(
            id=str(uuid4()),
            tool_id=str(manifest.id),
            version=manifest.version,
            manifest_json=manifest.model_dump(mode="json"),
            status="draft",
        )
        record.versions.append(version)
        self.tools[str(manifest.id)] = record
        return manifest

    def publish_tool(self, tool_id: str, signature: str) -> ToolRecord:
        record = self.tools[tool_id]
        if not signature:
            raise ValueError("publisher signature required")
        record.status = "published"
        record.signature = signature
        record.manifest.visibility = Visibility.marketplace
        record.versions[-1].status = "published"
        return record

    def list_tools(self, tag: str | None = None, max_price: float | None = None) -> list[ToolManifest]:
        results = [r.manifest for r in self.tools.values()]
        if tag:
            results = [m for m in results if tag in m.tags]
        if max_price is not None:
            results = [m for m in results if m.cost_core_energy <= max_price]
        return results

    def get_tool(self, tool_id: str) -> ToolRecord:
        return self.tools[tool_id]

    def log_usage(
        self,
        *,
        tool_id: str,
        caller_agent_id: str,
        status: str,
        cost: float,
        output: dict[str, Any] | None,
    ) -> UsageLog:
        entry = {
            "tool_id": tool_id,
            "caller_agent_id": caller_agent_id,
            "status": status,
            "cost": cost,
            "output": output,
            "ts": datetime.utcnow().isoformat(),
        }
        digest = hashlib.sha256((self._chain_hash + json.dumps(entry, sort_keys=True)).encode()).hexdigest()
        log = UsageLog(
            id=str(uuid4()),
            tool_id=tool_id,
            caller_agent_id=caller_agent_id,
            status=status,
            cost=cost,
            output=output,
            created_at=datetime.utcnow(),
            hash=digest,
        )
        self.usage_logs.append(log)
        self._chain_hash = digest
        return log

    def register_service(self, service_id: str, payload: dict[str, Any]) -> None:
        self.services[service_id] = payload

    def marketplace_tools(self) -> list[dict[str, Any]]:
        published = [r for r in self.tools.values() if r.status == "published"]
        out = []
        for record in published:
            ratings = [r.score for r in self.ratings if r.tool_id == str(record.manifest.id)]
            avg = sum(ratings) / len(ratings) if ratings else 0.0
            out.append(
                {
                    "tool": record.manifest.model_dump(mode="json"),
                    "rating": avg,
                    "revenue": record.revenue,
                }
            )
        return sorted(out, key=lambda item: (item["rating"], item["revenue"]), reverse=True)

    def purchase(self, tool_id: str, agent_id: str, model: str, amount: float) -> Purchase:
        purchase = Purchase(tool_id=tool_id, agent_id=agent_id, model=model, amount=amount)
        self.purchases.append(purchase)
        return purchase

    def add_rating(self, tool_id: str, agent_id: str, score: int, review: str) -> Rating:
        rating = Rating(tool_id=tool_id, agent_id=agent_id, score=score, review=review)
        self.ratings.append(rating)
        return rating


def role_allowed(manifest: ToolManifest, role: str, agent_id: str) -> bool:
    if not manifest.allowed_callers:
        return True
    return agent_id in manifest.allowed_callers or role in manifest.allowed_callers


def marketplace_fee(amount: float) -> float:
    return amount * settings.marketplace_fee_percent


ToolRegistry = Registry
