"""Lightweight SQLite ALTER TABLE migrations.

We do not pull in Alembic for a single-table prototype DB. On startup, the
app introspects existing columns and adds the new ones if missing. New
columns must be nullable so existing rows survive.
"""
from sqlalchemy import inspect, text
from ..database import engine


# (table, column, ddl-fragment after ADD COLUMN)
_MIGRATIONS: list[tuple[str, str, str]] = [
    ("materials", "parent_id", "parent_id TEXT"),
    ("materials", "mutation_directive", "mutation_directive TEXT"),
    ("materials", "source_session_id", "source_session_id TEXT"),
    ("materials", "source_corpus_id", "source_corpus_id TEXT"),
    ("sessions",  "player_token",     "player_token TEXT"),
    ("corpus_entries", "maturity_stage", "maturity_stage INTEGER"),
    ("genome_drafts", "field_type",              "field_type TEXT"),
    ("genome_drafts", "promoted",                "promoted TEXT DEFAULT 'no'"),
    ("genome_drafts", "promoted_genome",         "promoted_genome JSON"),
    ("genome_drafts", "source_seed_material_id", "source_seed_material_id TEXT"),
]


def run_migrations() -> list[str]:
    applied: list[str] = []
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, column, ddl in _MIGRATIONS:
            if not insp.has_table(table):
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if column in cols:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
            applied.append(f"{table}.{column}")
    return applied
