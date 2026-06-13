from fastapi import APIRouter, HTTPException
from ..services.genome_loader import (
    load_all_genomes, get_genome,
    list_runtime_genome_ids_from_db, get_promoted_genome_summary,
)
from ..schemas import GameListItem

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=list[GameListItem])
def list_games():
    out = [
        GameListItem(id=g.id, title=g.title, short_title=g.short_title, function=g.function)
        for g in load_all_genomes().values()
    ]
    for gid in list_runtime_genome_ids_from_db():
        s = get_promoted_genome_summary(gid)
        if s:
            out.append(GameListItem(**s))
    return out


@router.get("/{game_id}")
def get_game(game_id: str):
    g = get_genome(game_id)
    if not g:
        raise HTTPException(404, "unknown game")
    return g.model_dump()
