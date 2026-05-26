"""Google Sheets storage — dedup tab + posts tab. Single source of state.

Tabs:
  dedup:  url_hash | url | title | source | source_tier | seen_at | score | status
  posts:  posted_at_utc | posted_at_ny | url | title | score | fb_post_id | ig_post_id | ig_carousel_id

Read once per cycle, cache in memory, batched writes.

`InMemoryStore` provides the same interface without network; used by --smoke and
as a fallback when GOOGLE_SHEETS_ID is unset. That keeps the rest of the pipeline
runnable end-to-end while Meta + Google credentials are still being approved.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)

DEDUP_HEADERS = ["url_hash", "url", "title", "source", "source_tier", "seen_at", "score", "status"]
POSTS_HEADERS = ["posted_at_utc", "posted_at_ny", "url", "title", "score", "fb_post_id", "ig_post_id", "ig_carousel_id"]


@dataclass
class DedupRow:
    url_hash: str
    url: str
    title: str
    source: str
    source_tier: str
    seen_at: datetime
    score: float | None
    status: str   # "skipped" | "queued" | "published"


@dataclass
class PostRow:
    posted_at_utc: datetime
    posted_at_ny: datetime
    url: str
    title: str
    score: float
    fb_post_id: str
    ig_post_id: str
    ig_carousel_id: str


class Store(Protocol):
    def load_dedup(self) -> list[DedupRow]: ...
    def load_posts(self) -> list[PostRow]: ...
    def append_dedup(self, rows: list[DedupRow]) -> None: ...
    def append_post(self, row: PostRow) -> None: ...
    def posts_today_ny(self) -> int: ...


def _today_ny_count(rows: list[PostRow]) -> int:
    today = datetime.now(tz=ZoneInfo("America/New_York")).date()
    return sum(1 for r in rows if r.posted_at_ny.date() == today)


class InMemoryStore:
    """Process-local store. Smoke-mode and offline fallback."""

    def __init__(self):
        self._dedup: list[DedupRow] = []
        self._posts: list[PostRow] = []

    def load_dedup(self) -> list[DedupRow]:
        return list(self._dedup)

    def load_posts(self) -> list[PostRow]:
        return list(self._posts)

    def append_dedup(self, rows: list[DedupRow]) -> None:
        self._dedup.extend(rows)

    def append_post(self, row: PostRow) -> None:
        self._posts.append(row)

    def posts_today_ny(self) -> int:
        return _today_ny_count(self._posts)


class SheetsClient:
    """Wraps gspread with run-scoped caching."""

    def __init__(self, sheets_id: str, service_account_json: dict[str, Any]):
        self.sheets_id = sheets_id
        self._sa = service_account_json
        self._dedup_cache: list[DedupRow] | None = None
        self._posts_cache: list[PostRow] | None = None
        self._gc = None
        self._sh = None

    def _open(self):
        if self._sh is not None:
            return self._sh
        import gspread
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(
            self._sa,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        self._gc = gspread.authorize(creds)
        self._sh = self._gc.open_by_key(self.sheets_id)
        self._ensure_tab("dedup", DEDUP_HEADERS)
        self._ensure_tab("posts", POSTS_HEADERS)
        return self._sh

    def _ensure_tab(self, name: str, headers: list[str]) -> None:
        sh = self._sh
        try:
            ws = sh.worksheet(name)
        except Exception:
            ws = sh.add_worksheet(title=name, rows=1000, cols=max(8, len(headers)))
        first = ws.row_values(1)
        if first != headers:
            ws.update("A1", [headers])

    def load_dedup(self) -> list[DedupRow]:
        if self._dedup_cache is not None:
            return self._dedup_cache
        sh = self._open()
        rows = sh.worksheet("dedup").get_all_records()
        out: list[DedupRow] = []
        for r in rows:
            try:
                out.append(DedupRow(
                    url_hash=str(r["url_hash"]),
                    url=str(r["url"]),
                    title=str(r["title"]),
                    source=str(r["source"]),
                    source_tier=str(r["source_tier"]),
                    seen_at=datetime.fromisoformat(str(r["seen_at"])),
                    score=float(r["score"]) if r.get("score") not in ("", None) else None,
                    status=str(r["status"]),
                ))
            except Exception as exc:
                log.warning("bad dedup row %s: %s", r, exc)
        self._dedup_cache = out
        return out

    def load_posts(self) -> list[PostRow]:
        if self._posts_cache is not None:
            return self._posts_cache
        sh = self._open()
        rows = sh.worksheet("posts").get_all_records()
        out: list[PostRow] = []
        for r in rows:
            try:
                out.append(PostRow(
                    posted_at_utc=datetime.fromisoformat(str(r["posted_at_utc"])),
                    posted_at_ny=datetime.fromisoformat(str(r["posted_at_ny"])),
                    url=str(r["url"]),
                    title=str(r["title"]),
                    score=float(r["score"]),
                    fb_post_id=str(r.get("fb_post_id", "")),
                    ig_post_id=str(r.get("ig_post_id", "")),
                    ig_carousel_id=str(r.get("ig_carousel_id", "")),
                ))
            except Exception as exc:
                log.warning("bad post row %s: %s", r, exc)
        self._posts_cache = out
        return out

    def append_dedup(self, rows: list[DedupRow]) -> None:
        if not rows:
            return
        sh = self._open()
        values = [[
            r.url_hash, r.url, r.title, r.source, r.source_tier,
            r.seen_at.isoformat(), r.score if r.score is not None else "", r.status,
        ] for r in rows]
        sh.worksheet("dedup").append_rows(values, value_input_option="RAW")
        if self._dedup_cache is not None:
            self._dedup_cache.extend(rows)

    def append_post(self, row: PostRow) -> None:
        sh = self._open()
        values = [[
            row.posted_at_utc.isoformat(), row.posted_at_ny.isoformat(),
            row.url, row.title, row.score,
            row.fb_post_id, row.ig_post_id, row.ig_carousel_id,
        ]]
        sh.worksheet("posts").append_rows(values, value_input_option="RAW")
        if self._posts_cache is not None:
            self._posts_cache.append(row)

    def posts_today_ny(self) -> int:
        return _today_ny_count(self.load_posts())


def build_store(sheets_id: str, service_account_json: dict[str, Any] | None) -> Store:
    if not sheets_id or not service_account_json:
        log.warning("sheets creds missing — using in-memory store (run-local state)")
        return InMemoryStore()
    return SheetsClient(sheets_id, service_account_json)


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
