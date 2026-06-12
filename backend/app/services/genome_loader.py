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
    return load_all_genomes().get(game_id)


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
