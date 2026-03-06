from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Store:
    agents: dict[str, dict[str, Any]] = field(default_factory=dict)
    wallets: dict[str, dict[str, Any]] = field(default_factory=dict)
    transactions: list[dict[str, Any]] = field(default_factory=list)
    core_energy_ledger: dict[str, float] = field(default_factory=dict)
    proofs: dict[str, dict[str, Any]] = field(default_factory=dict)
    regions: dict[str, dict[str, Any]] = field(default_factory=dict)
    central_banks: dict[str, dict[str, Any]] = field(default_factory=dict)
    organizations: dict[str, dict[str, Any]] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    quotas: dict[str, dict[str, float]] = field(default_factory=dict)

    def append_log(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        prev = self.logs[-1]["hash"] if self.logs else "GENESIS"
        stamp = time.time()
        serialized = json.dumps({"prev": prev, "action": action, "payload": payload, "t": stamp}, sort_keys=True)
        digest = hashlib.sha256(serialized.encode()).hexdigest()
        row = {"timestamp": stamp, "action": action, "payload": payload, "prev_hash": prev, "hash": digest}
        self.logs.append(row)
        return row

    def persist_receipt(self, directory: str, filename: str, payload: dict[str, Any]) -> str:
        p = Path(directory)
        p.mkdir(parents=True, exist_ok=True)
        target = p / filename
        target.write_text(json.dumps(payload, indent=2))
        return str(target)


store = Store()
