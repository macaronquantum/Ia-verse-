#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio

from app.config import settings
from app.llm.local_manager import LocalModelManager


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--quant", default="4bit")
    parser.add_argument("--cache-dir", default=settings.MODEL_CACHE_DIR)
    args = parser.parse_args()

    manager = LocalModelManager(cache_dir=args.cache_dir)
    names = [args.model] if args.model else [m["name"] for m in settings.LOCAL_MODELS]
    if not args.all and not args.model:
        names = names[:1]
    for name in names:
        path = await manager.download_model(name, quant=args.quant)
        print(f"downloaded {name} -> {path}")


if __name__ == "__main__":
    asyncio.run(main())
