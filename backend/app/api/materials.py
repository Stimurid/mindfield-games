from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Material
from ..services.translation import translate_text, translate_material_payload

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("")
def list_materials(gameId: str | None = None, lang: str = Query("ru"),
                   db: Session = Depends(get_db)):
    q = db.query(Material)
    if gameId:
        q = q.filter(Material.game_id == gameId)
    out = [
        {"id": m.id, "game_id": m.game_id, "title": m.title, "namespace": m.namespace}
        for m in q.order_by(Material.namespace.desc(), Material.created_at.asc()).all()
    ]
    if lang != "ru":
        for r in out:
            r["title"] = translate_text(r["title"], lang, db)
    return out


@router.get("/{material_id}")
def get_material(material_id: str, lang: str = Query("ru"), db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "no material")
    out = {
        "id": m.id,
        "game_id": m.game_id,
        "title": m.title,
        "namespace": m.namespace,
        "payload": m.payload,
        "parent_id": m.parent_id,
        "mutation_directive": m.mutation_directive,
        "source_session_id": m.source_session_id,
        "source_corpus_id": m.source_corpus_id,
    }
    if lang != "ru":
        out["title"] = translate_text(out["title"], lang, db)
        out["payload"] = translate_material_payload(out["payload"], lang, db)
        if out["mutation_directive"]:
            out["mutation_directive"] = translate_text(out["mutation_directive"], lang, db)
    return out
