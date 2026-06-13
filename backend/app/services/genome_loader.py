import json
from pathlib import Path
from functools import lru_cache
from ..schemas import GameGenome

_ROOT = Path(__file__).resolve().parent.parent.parent
GENOME_DIR = _ROOT / "game_genomes"
SEED_DIRS = [_ROOT / "seed_materials", _ROOT / "seed_materials_real"]


@lru_cache(maxsize=1)
def load_all_genomes() -> dict[str, GameGenome]:
    genomes: dict[str, GameGenome] = {}
    for fp in GENOME_DIR.glob("*.json"):
        data = json.loads(fp.read_text(encoding="utf-8"))
        g = GameGenome(**data)
        genomes[g.id] = g
    return genomes


def get_genome(game_id: str) -> GameGenome | None:
    g = load_all_genomes().get(game_id)
    if g:
        return g
    # Promoted draft? Resolve via DB. Imported here to avoid a circular import
    # at module-load time.
    if game_id.startswith("promoted_"):
        from ..database import SessionLocal
        from ..models import GenomeDraft
        db = SessionLocal()
        try:
            draft_id = game_id.removeprefix("promoted_")
            d = db.query(GenomeDraft).filter(GenomeDraft.id == draft_id).first()
            if d and d.promoted == "yes" and d.promoted_genome:
                return GameGenome(**d.promoted_genome)
        finally:
            db.close()
    return None


def list_runtime_genome_ids_from_db() -> list[str]:
    """Promoted drafts that count as runtime games. Used by /api/games."""
    from ..database import SessionLocal
    from ..models import GenomeDraft
    db = SessionLocal()
    try:
        rows = db.query(GenomeDraft).filter(GenomeDraft.promoted == "yes").all()
        return [f"promoted_{d.id}" for d in rows]
    finally:
        db.close()


def get_promoted_genome_summary(game_id: str) -> dict | None:
    """For /api/games listing — return enough to render the game tile."""
    if not game_id.startswith("promoted_"):
        return None
    from ..database import SessionLocal
    from ..models import GenomeDraft
    db = SessionLocal()
    try:
        draft_id = game_id.removeprefix("promoted_")
        d = db.query(GenomeDraft).filter(GenomeDraft.id == draft_id).first()
        if not d or d.promoted != "yes" or not d.promoted_genome:
            return None
        g = d.promoted_genome
        return {
            "id": g["id"], "title": g["title"], "short_title": g.get("short_title", g["title"]),
            "function": g.get("function", ""),
        }
    finally:
        db.close()


def load_seed_materials() -> list[dict]:
    out = []
    for base in SEED_DIRS:
        if not base.exists():
            continue
        for sub in base.iterdir():
            if not sub.is_dir():
                continue
            for fp in sub.glob("*.json"):
                data = json.loads(fp.read_text(encoding="utf-8"))
                data.setdefault("namespace", "demo" if base.name == "seed_materials" else "real")
                out.append(data)
    return out
