"""Idempotent corpus ingest. Run on startup; safe to re-run."""
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..models import CorpusEntry
from ..database import SessionLocal, engine
from .corpus_parser import parse_corpus, parse_phase_docs


def _ensure_fts5() -> None:
    """SQLite FTS5 virtual table mirrors title/body_md for fast search.

    Synchronised via triggers so we don't have to think about it after this.
    """
    with engine.begin() as conn:
        # No external content — we maintain corpus_fts manually via triggers.
        # This avoids the FTS5 'content=...' column-name coupling.
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
                title, body, code UNINDEXED, kind UNINDEXED
            )
        """))
        for trig in ("corpus_ai", "corpus_ad", "corpus_au"):
            conn.execute(text(f"DROP TRIGGER IF EXISTS {trig}"))
        conn.execute(text("""
            CREATE TRIGGER corpus_ai AFTER INSERT ON corpus_entries BEGIN
                INSERT INTO corpus_fts(rowid, title, body, code, kind)
                VALUES (new.rowid, new.title, new.body_md, new.code, new.kind);
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER corpus_ad AFTER DELETE ON corpus_entries BEGIN
                DELETE FROM corpus_fts WHERE rowid = old.rowid;
            END
        """))
        conn.execute(text("""
            CREATE TRIGGER corpus_au AFTER UPDATE ON corpus_entries BEGIN
                DELETE FROM corpus_fts WHERE rowid = old.rowid;
                INSERT INTO corpus_fts(rowid, title, body, code, kind)
                VALUES (new.rowid, new.title, new.body_md, new.code, new.kind);
            END
        """))


def _backfill_fts5(db: Session) -> None:
    """Make sure existing rows are indexed (initial run after triggers exist)."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM corpus_fts"))
        conn.execute(text("""
            INSERT INTO corpus_fts(rowid, title, body, code, kind)
            SELECT rowid, title, body_md, code, kind FROM corpus_entries
        """))


def ingest_corpus_if_needed() -> dict:
    """Parse spec.md + phase docs and persist if the corpus is empty or stale.

    Re-runs when a new top-level entry would appear (count comparison only).
    """
    _ensure_fts5()
    # Local dev: docs/ sits at repo root (one up from backend/).
    # Production container: docs/ is bind-mounted at /docs by compose.
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "docs",
        Path("/docs"),
    ]
    docs_dir = next((d for d in candidates if (d / "spec.md").exists() or d.exists()), candidates[0])
    spec_path = docs_dir / "spec.md"

    entries: list[dict] = []
    entries.extend(parse_corpus(spec_path))
    entries.extend(parse_phase_docs(docs_dir))

    if not entries:
        return {"ingested": 0, "skipped": "no source files"}

    db: Session = SessionLocal()
    try:
        existing = {e.code for e in db.query(CorpusEntry).all()}
        new_count = 0
        for e in entries:
            if e["code"] in existing:
                continue
            db.add(CorpusEntry(**e))
            new_count += 1
        if new_count:
            db.commit()
            _backfill_fts5(db)
        return {"ingested": new_count, "total": db.query(CorpusEntry).count()}
    finally:
        db.close()
