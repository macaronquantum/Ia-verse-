"""Simple vector store adapter with pluggable backend semantics."""

from __future__ import annotations


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.rows: dict[str, tuple[list[float], dict]] = {}

    def embed(self, text: str) -> list[float]:
        tokens = [float((ord(ch) % 32) / 31.0) for ch in text[:16]]
        return tokens + [0.0] * (16 - len(tokens))

    def upsert(self, row_id: str, vector: list[float], metadata: dict) -> None:
        self.rows[row_id] = (vector, metadata)

    def query(self, vector: list[float], k: int) -> list[dict]:
        def score(v: list[float]) -> float:
            return sum(a * b for a, b in zip(v, vector))

        ranked = sorted(self.rows.items(), key=lambda item: score(item[1][0]), reverse=True)
        return [dict(id=row_id, metadata=data[1]) for row_id, data in ranked[:k]]
