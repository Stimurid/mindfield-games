"""Phase 16: lightweight admin CRUD for materials.

No app-level auth — the production deployment lives behind Caddy basic_auth,
and the local dev surface is intentionally open. If/when accounts ship,
this router gets a require_admin dependency.
"""
import re
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Any
from ..database import get_db
from ..models import Material, Organ
from ..services.organ_seed import BANK_LABEL
from ..api.triage import FATES, FATE_LABEL
from ..services.operator_profile import _BIAS_MEANING, _CROSS_PATTERNS


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


# ── Ontology: organs CRUD ────────────────────────────────────────────────────
def _slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[ /]+", "_", s)
    s = re.sub(r"[^a-zа-яё0-9_]", "", s)
    return s or "_"


class OrganIn(BaseModel):
    bank: str
    name: str
    description: Optional[str] = None


class OrganPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bank: Optional[str] = None


@router.get("/organs")
def admin_list_organs(db: Session = Depends(get_db), bank: Optional[str] = None):
    q = db.query(Organ)
    if bank:
        q = q.filter(Organ.bank == bank)
    rows = q.order_by(Organ.bank, Organ.source.asc(), Organ.name).all()
    return [
        {
            "id": o.id, "bank": o.bank, "code": o.code, "name": o.name,
            "description": o.description, "source": o.source,
            "source_entry_id": o.source_entry_id,
            "created_at": o.created_at.isoformat() + "Z" if o.created_at else None,
        }
        for o in rows
    ]


@router.post("/organs")
def admin_create_organ(payload: OrganIn, db: Session = Depends(get_db)):
    if payload.bank not in BANK_LABEL:
        raise HTTPException(400, f"bank must be one of {list(BANK_LABEL.keys())}")
    if not payload.name.strip():
        raise HTTPException(400, "name required")
    code = f"{payload.bank}.{_slug(payload.name)}_admin"
    existing = db.query(Organ).filter(Organ.code == code).first()
    if existing:
        raise HTTPException(409, "organ with this name already exists in bank")
    o = Organ(
        bank=payload.bank, code=code, name=payload.name.strip(),
        description=payload.description, source="admin_authored",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return {"id": o.id, "bank": o.bank, "code": o.code, "name": o.name,
            "description": o.description, "source": o.source}


@router.patch("/organs/{organ_id}")
def admin_update_organ(organ_id: str, payload: OrganPatch, db: Session = Depends(get_db)):
    o = db.query(Organ).filter(Organ.id == organ_id).first()
    if not o:
        raise HTTPException(404, "no such organ")
    if o.source == "canon_v0.1":
        raise HTTPException(409, "canonical organs are immutable; create an admin_authored override instead")
    if payload.name is not None: o.name = payload.name
    if payload.description is not None: o.description = payload.description
    if payload.bank is not None:
        if payload.bank not in BANK_LABEL:
            raise HTTPException(400, "bad bank")
        o.bank = payload.bank
    db.commit()
    db.refresh(o)
    return {"id": o.id, "bank": o.bank, "code": o.code, "name": o.name,
            "description": o.description, "source": o.source}


@router.delete("/organs/{organ_id}")
def admin_delete_organ(organ_id: str, db: Session = Depends(get_db)):
    o = db.query(Organ).filter(Organ.id == organ_id).first()
    if not o:
        raise HTTPException(404, "no such organ")
    if o.source == "canon_v0.1":
        raise HTTPException(409, "canonical organs cannot be deleted")
    db.delete(o)
    db.commit()
    return {"deleted": organ_id}


# ── Ontology: read-only fates and cross-patterns ────────────────────────────

@router.get("/ontology/fates")
def admin_list_fates():
    """Triage fates are code-defined. To edit: backend/app/api/triage.py."""
    return {
        "fates": [{"fate": f, "label": FATE_LABEL[f]} for f in FATES],
        "source_file": "backend/app/api/triage.py",
        "editable": False,
    }


@router.get("/ontology/cross-patterns")
def admin_list_cross_patterns():
    """Operator Profile cross-patterns are code-defined.
    To edit: backend/app/services/operator_profile.py."""
    patterns = []
    for needed, name in _CROSS_PATTERNS:
        patterns.append({
            "name": name,
            "needed_dimensions": [{"game_id": g, "value": v} for g, v in sorted(needed)],
        })
    return {
        "patterns": patterns,
        "bias_meanings": [
            {"game_id": g, "value": v, "meaning": m}
            for (g, v), m in _BIAS_MEANING.items()
        ],
        "source_file": "backend/app/services/operator_profile.py",
        "editable": False,
    }
