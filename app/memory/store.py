from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ShortTermMemory:
    events: list[str] = field(default_factory=list)


@dataclass
class LongTermMemory:
    summaries: list[str] = field(default_factory=list)


@dataclass
class EconomicHistory:
    pnl_series: list[float] = field(default_factory=list)
    major_events: list[str] = field(default_factory=list)


class MemoryCompressor:
    def compress(self, stm: ShortTermMemory, ltm: LongTermMemory, econ: EconomicHistory) -> str:
        summary = f"events={len(stm.events)} pnl_points={len(econ.pnl_series)}"
        ltm.summaries.append(summary)
        stm.events.clear()
        return summary

    def postmortem(self, econ: EconomicHistory, reason: str) -> str:
        text = f"postmortem:{reason}:events={len(econ.major_events)}"
        econ.major_events.append(text)
        return text
