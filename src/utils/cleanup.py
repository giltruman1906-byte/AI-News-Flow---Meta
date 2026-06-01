"""Delete published slides older than the retention window.

Cleans both:
  - Local `published/` directory
  - GitHub `published` branch (date-prefixed folders like YYYY/MM/DD/)

Intended to run on a weekend schedule (Sat/Sun) via GitHub Actions.
Default retention: 7 days.
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

log = logging.getLogger(__name__)

PUBLISHED_DIR = Path(__file__).resolve().parent.parent.parent / "published"


def cleanup_local(retention_days: int = 7, base_dir: Path | None = None) -> int:
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
            log.info("removed local %s (modified %s)", entry.name, mtime.date())
            removed += 1

    log.info("local cleanup — removed %d items, retention=%d days", removed, retention_days)
    return removed


def _gh_list_dir(repo: str, branch: str, path: str, token: str) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    r = httpx.get(url, params={"ref": branch}, headers=headers, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    return r.json()


def _gh_delete_file(repo: str, branch: str, path: str, sha: str, token: str) -> None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    body = {"message": f"cleanup: remove {path}", "sha": sha, "branch": branch}
    r = httpx.request("DELETE", url, json=body, headers=headers, timeout=30)
    r.raise_for_status()


def cleanup_github(repo: str, branch: str, token: str, retention_days: int = 7) -> int:
    """Delete date-prefixed folders (YYYY/MM/DD/) older than retention from the GitHub branch."""
    if not repo or not token:
        log.info("github cleanup skipped — repo or token not configured")
        return 0

    cutoff = date.today() - timedelta(days=retention_days)
    removed = 0

    years = _gh_list_dir(repo, branch, "", token)
    for year_entry in years:
        if year_entry["type"] != "dir" or not year_entry["name"].isdigit():
            continue
        year = int(year_entry["name"])
        if year > cutoff.year:
            continue

        months = _gh_list_dir(repo, branch, year_entry["name"], token)
        for month_entry in months:
            if month_entry["type"] != "dir" or not month_entry["name"].isdigit():
                continue
            month = int(month_entry["name"])
            if year == cutoff.year and month > cutoff.month:
                continue

            days = _gh_list_dir(repo, branch, f"{year_entry['name']}/{month_entry['name']}", token)
            for day_entry in days:
                if day_entry["type"] != "dir" or not day_entry["name"].isdigit():
                    continue
                try:
                    folder_date = date(year, month, int(day_entry["name"]))
                except ValueError:
                    continue
                if folder_date >= cutoff:
                    continue

                day_path = f"{year_entry['name']}/{month_entry['name']}/{day_entry['name']}"
                removed += _delete_tree(repo, branch, day_path, token)
                log.info("removed github %s (older than %s)", day_path, cutoff)

    log.info("github cleanup — removed %d files, retention=%d days", removed, retention_days)
    return removed


def _delete_tree(repo: str, branch: str, path: str, token: str) -> int:
    """Recursively delete all files under a path on the GitHub branch."""
    removed = 0
    entries = _gh_list_dir(repo, branch, path, token)
    for entry in entries:
        if entry["type"] == "dir":
            removed += _delete_tree(repo, branch, entry["path"], token)
        else:
            _gh_delete_file(repo, branch, entry["path"], entry["sha"], token)
            removed += 1
    return removed


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Clean up old published slides")
    parser.add_argument("--retention-days", type=int, default=7)
    parser.add_argument("--dir", type=str, default=None, help="Override local published dir")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

    base = Path(args.dir) if args.dir else None
    cleanup_local(args.retention_days, base)

    repo = os.getenv("GITHUB_REPO", "")
    branch = os.getenv("GITHUB_PUBLISHED_BRANCH", "published")
    token = os.getenv("GITHUB_TOKEN", "")
    cleanup_github(repo, branch, token, args.retention_days)


if __name__ == "__main__":
    main()
