from __future__ import annotations

import asyncio
import json

from app.simulation import build_default_engine


async def main() -> None:
    engine = build_default_engine()
    result = await engine.run(ticks=6, tick_seconds=0.01)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
