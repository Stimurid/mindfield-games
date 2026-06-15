from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.genome_loader import (
    load_all_genomes, get_genome,
    list_runtime_genome_ids_from_db, get_promoted_genome_summary,
)
from ..services.translation import translate_dict, GAME_PATHS, translate_text, translate_strings_batch

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
def list_games(lang: str = Query("ru"), db: Session = Depends(get_db)):
    out = []
    for g in load_all_genomes().values():
        out.append({
            "id": g.id,
            "title": g.title,
            "short_title": g.short_title,
            "function": g.function,
        })
    for gid in list_runtime_genome_ids_from_db():
        s = get_promoted_genome_summary(gid)
        if s:
            out.append(s)
    if lang != "ru":
        # Single batch lookup + parallel LLM for whatever's not yet cached.
        strings = [v for r in out for v in (r["title"], r["short_title"], r["function"]) if v]
        table = translate_strings_batch(strings, lang, db)
        for r in out:
            r["title"] = table.get(r["title"], r["title"])
            r["short_title"] = table.get(r["short_title"], r["short_title"])
            r["function"] = table.get(r["function"], r["function"])
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
