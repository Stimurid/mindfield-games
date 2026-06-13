"""Phase 16: lightweight admin CRUD for materials.

No app-level auth — the production deployment lives behind Caddy basic_auth,
and the local dev surface is intentionally open. If/when accounts ship,
this router gets a require_admin dependency.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any
from ..database import get_db
from ..models import Material


router = APIRouter(prefix="/api/admin", tags=["admin"])


class MaterialIn(BaseModel):
    game_id: str
    title: str
    payload: dict[str, Any]
    namespace: str = "demo"


class MaterialPatch(BaseModel):
    title: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    namespace: Optional[str] = None


@router.get("/materials")
def list_all(db: Session = Depends(get_db)):
    rows = db.query(Material).order_by(Material.game_id, Material.namespace.desc(),
                                        Material.created_at.desc()).all()
    return [_serialize(m) for m in rows]


@router.post("/materials")
def create_material(payload: MaterialIn, db: Session = Depends(get_db)):
    m = Material(
        game_id=payload.game_id,
        title=payload.title,
        namespace=payload.namespace,
        payload=payload.payload,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _serialize(m)


@router.put("/materials/{material_id}")
def update_material(material_id: str, payload: MaterialPatch, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "no such material")
    if payload.title is not None:
        m.title = payload.title
    if payload.payload is not None:
        m.payload = payload.payload
    if payload.namespace is not None:
        m.namespace = payload.namespace
    db.commit()
    db.refresh(m)
    return _serialize(m)


@router.delete("/materials/{material_id}")
def delete_material(material_id: str, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "no such material")
    db.delete(m)
    db.commit()
    return {"deleted": material_id}


def _serialize(m: Material) -> dict:
    return {
        "id": m.id,
        "game_id": m.game_id,
        "title": m.title,
        "namespace": m.namespace,
        "payload": m.payload,
        "parent_id": m.parent_id,
        "source_corpus_id": m.source_corpus_id,
        "mutation_directive": m.mutation_directive,
        "created_at": m.created_at.isoformat() + "Z" if m.created_at else None,
    }
