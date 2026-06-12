from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Material

router = APIRouter(prefix="/api/materials", tags=["materials"])


@router.get("")
def list_materials(gameId: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Material)
    if gameId:
        q = q.filter(Material.game_id == gameId)
    return [
        {"id": m.id, "game_id": m.game_id, "title": m.title}
        for m in q.all()
    ]


@router.get("/{material_id}")
def get_material(material_id: str, db: Session = Depends(get_db)):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "no material")
    return {"id": m.id, "game_id": m.game_id, "title": m.title, "payload": m.payload}
