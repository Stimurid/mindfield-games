from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.genome_loader import (
    load_all_genomes, get_genome,
    list_runtime_genome_ids_from_db, get_promoted_genome_summary,
)
from ..services.translation import translate_dict, GAME_PATHS, translate_text

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
def list_games(lang: str = Query("ru"), db: Session = Depends(get_db)):
    out = []
    for g in load_all_genomes().values():
        item = {
            "id": g.id,
            "title": g.title,
            "short_title": g.short_title,
            "function": g.function,
        }
        if lang != "ru":
            item["title"] = translate_text(item["title"], lang, db)
            item["short_title"] = translate_text(item["short_title"], lang, db)
            item["function"] = translate_text(item["function"], lang, db)
        out.append(item)
    for gid in list_runtime_genome_ids_from_db():
        s = get_promoted_genome_summary(gid)
        if not s:
            continue
        if lang != "ru":
            s["title"] = translate_text(s["title"], lang, db)
            s["short_title"] = translate_text(s["short_title"], lang, db)
            s["function"] = translate_text(s["function"], lang, db)
        out.append(s)
    return out


@router.get("/{game_id}")
def get_game(game_id: str, lang: str = Query("ru"), db: Session = Depends(get_db)):
    g = get_genome(game_id)
    if not g:
        raise HTTPException(404, "unknown game")
    data = g.model_dump()
    if lang != "ru":
        data = translate_dict(data, GAME_PATHS, lang, db)
    return data
