"""Phase 15: maturity stage backfill for corpus entries.

Defaults follow §3 'Стадии зрелости': 0 raw → 5 school/platform.
A null value means 'unset' — UI shows it neutrally. The backfill ONLY
fills nulls; explicit values set by designers stay untouched.
"""
from sqlalchemy import update
from sqlalchemy.orm import Session
from ..models import CorpusEntry
from ..database import SessionLocal


# Best-guess defaults per kind. They can be revised per entry via PATCH.
DEFAULT_BY_KIND: dict[str, int] = {
    "source_card":    0,   # сырой фрагмент
    "source_section": 0,
    "micro_bullet":   0,
    "micro_numbered": 0,
    "phase_doc":      1,   # упражнение в нашей разработке
    "micro_aspect":   1,
    "residual":       1,
    "precard":        2,   # игра-упражнение (7 канонических карточек)
    "micro_game":     2,
    "chimera":        2,
    "breed":          3,   # психотехническая игра (рабочая порода)
    "genome":         3,
    "appspec":        3,
    "attractor":      4,   # коэволюционный симулятор формы
    "r_root":         4,
}


def backfill_default_maturity() -> dict:
    """Set maturity_stage from DEFAULT_BY_KIND on rows where it is still NULL.
    Idempotent: explicitly-set values are preserved.
    """
    db: Session = SessionLocal()
    try:
        applied = 0
        for kind, stage in DEFAULT_BY_KIND.items():
            r = db.execute(
                update(CorpusEntry)
                .where(CorpusEntry.kind == kind)
                .where(CorpusEntry.maturity_stage.is_(None))
                .values(maturity_stage=stage)
            )
            applied += r.rowcount or 0
        if applied:
            db.commit()
        return {"applied": applied}
    finally:
        db.close()
