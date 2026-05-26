"""Delete published slides older than the retention window.

Intended to run on a weekend schedule (Sat/Sun) via GitHub Actions or cron.
Default retention: 7 days.
"""
from __future__ import annotations

import argparse
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger(__name__)

PUBLISHED_DIR = Path(__file__).resolve().parent.parent.parent / "published"


def cleanup(retention_days: int = 7, base_dir: Path | None = None) -> int:
    target = base_dir or PUBLISHED_DIR
    if not target.exists():
        log.info("published dir does not exist: %s", target)
        return 0

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    removed = 0

    for entry in sorted(target.iterdir()):
        if entry.name.startswith("."):
            continue
        mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            log.info("removed %s (modified %s)", entry.name, mtime.date())
            removed += 1

    log.info("cleanup done — removed %d items, retention=%d days", removed, retention_days)
    return removed


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Clean up old published slides")
    parser.add_argument("--retention-days", type=int, default=7)
    parser.add_argument("--dir", type=str, default=None, help="Override published dir")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

    base = Path(args.dir) if args.dir else None
    cleanup(args.retention_days, base)


if __name__ == "__main__":
    main()
