from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from ..database import get_db, engine
from ..models import CorpusEntry, CorpusLink

router = APIRouter(prefix="/api/library", tags=["library"])


_KIND_LABEL = {
    "attractor":  "Аттракторы",
    "r_root":     "Корневые операционные аттракторы",
    "breed":      "Породы",
    "chimera":    "Химерная матрица",
    "precard":    "Карточки 1-7",
    "residual":   "Остатки",
    "genome":     "Геномы первых четырёх",
    "appspec":    "App-spec",
    "phase_doc":  "Документы фаз разработки",
}


@router.get("/sections")
def list_sections(db: Session = Depends(get_db)):
    rows = (
        db.query(CorpusEntry.kind, func.count(CorpusEntry.id))
        .group_by(CorpusEntry.kind)
        .all()
    )
    return [
        {"kind": k, "label": _KIND_LABEL.get(k, k), "count": c}
        for k, c in sorted(rows, key=lambda r: list(_KIND_LABEL.keys()).index(r[0]) if r[0] in _KIND_LABEL else 99)
    ]


@router.get("/entries")
def list_entries(
    db: Session = Depends(get_db),
    kind: str | None = None,
    pass_filter: str | None = Query(None, alias="pass"),
    limit: int = 500,
):
    q = db.query(CorpusEntry)
    if kind:
        q = q.filter(CorpusEntry.kind == kind)
    if pass_filter:
        q = q.filter(CorpusEntry.source_pass == pass_filter)
    rows = q.order_by(CorpusEntry.kind, CorpusEntry.order_key, CorpusEntry.code).limit(limit).all()
    return [
        {
            "id": e.id,
            "code": e.code,
            "kind": e.kind,
            "title": e.title,
            "source_pass": e.source_pass,
            "source_line": e.source_line,
        }
        for e in rows
    ]


@router.get("/entries/{entry_id}")
def get_entry(entry_id: str, db: Session = Depends(get_db)):
    e = db.query(CorpusEntry).filter(CorpusEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "no such corpus entry")
    parents = (
        db.query(CorpusEntry, CorpusLink.relation)
        .join(CorpusLink, CorpusLink.parent_id == CorpusEntry.id)
        .filter(CorpusLink.child_id == e.id)
        .all()
    )
    children = (
        db.query(CorpusEntry, CorpusLink.relation)
        .join(CorpusLink, CorpusLink.child_id == CorpusEntry.id)
        .filter(CorpusLink.parent_id == e.id)
        .all()
    )
    return {
        "id": e.id,
        "code": e.code,
        "kind": e.kind,
        "title": e.title,
        "body_md": e.body_md,
        "source_pass": e.source_pass,
        "source_line": e.source_line,
        "parents":  [{"id": p[0].id, "code": p[0].code, "title": p[0].title, "relation": p[1]} for p in parents],
        "children": [{"id": c[0].id, "code": c[0].code, "title": c[0].title, "relation": c[1]} for c in children],
    }


@router.get("/search")
def search(q: str = Query(min_length=2), limit: int = 50, kind: str | None = None):
    # FTS5 expects a MATCH expression. Quote literally to avoid syntax errors.
    safe = q.replace('"', '""')
    fts_query = f'"{safe}"'
    sql = text(
        "SELECT e.id, e.code, e.kind, e.title, "
        "       snippet(corpus_fts, 1, '<mark>', '</mark>', '…', 18) AS snippet "
        "FROM corpus_fts JOIN corpus_entries e ON e.rowid = corpus_fts.rowid "
        "WHERE corpus_fts MATCH :q "
        + ("AND e.kind = :kind " if kind else "")
        + "ORDER BY rank LIMIT :limit"
    )
    with engine.connect() as conn:
        params = {"q": fts_query, "limit": limit}
        if kind:
            params["kind"] = kind
        rows = conn.execute(sql, params).fetchall()
    return [
        {"id": r[0], "code": r[1], "kind": r[2], "title": r[3], "snippet": r[4]}
        for r in rows
    ]
