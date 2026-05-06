#!/usr/bin/env python3
"""
Long-running daemon that fires the AI digest once per day at a configured hour.
Usage:  python3 scheduler.py [--hour 7] [--minute 0]
The process can be backgrounded with nohup or screen.
"""
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path


def next_run(hour: int, minute: int) -> datetime:
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target


def run_digest(script: Path) -> None:
    print(f"\n[scheduler] Firing digest at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script.parent),
        capture_output=False,
    )
    if result.returncode != 0:
        print(f"[scheduler] Digest exited with code {result.returncode}")
    else:
        print(f"[scheduler] Digest finished OK")


def main():
    parser = argparse.ArgumentParser(description="AI News Digest — daily scheduler")
    parser.add_argument("--hour",   type=int, default=7, help="Hour to run (24h, default 7)")
    parser.add_argument("--minute", type=int, default=0, help="Minute to run (default 0)")
    args = parser.parse_args()

    script = Path(__file__).parent / "main.py"
    print(f"[scheduler] Will run digest daily at {args.hour:02d}:{args.minute:02d}")

    while True:
        target = next_run(args.hour, args.minute)
        wait_sec = (target - datetime.now()).total_seconds()
        print(f"[scheduler] Next run at {target.strftime('%Y-%m-%d %H:%M:%S')} "
              f"(in {wait_sec/3600:.1f}h)", flush=True)
        time.sleep(max(wait_sec, 1))
        run_digest(script)


if __name__ == "__main__":
    main()
