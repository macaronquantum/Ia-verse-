from __future__ import annotations

import argparse
import time

from app.oracles.jobs import process_jobs_tick


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tick-seconds", type=float, default=5)
    args = parser.parse_args()
    while True:
        process_jobs_tick()
        time.sleep(args.tick_seconds)


if __name__ == "__main__":
    main()
