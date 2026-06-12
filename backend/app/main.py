from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import init_db, SessionLocal
from .models import Material
from .services.genome_loader import load_seed_materials, load_all_genomes
from .api import games, sessions, materials, llm as llm_api


def seed_materials_if_empty():
    db: Session = SessionLocal()
    try:
        if db.query(Material).count() > 0:
            return
        for seed in load_seed_materials():
            db.add(Material(
                id=seed["id"],
                game_id=seed["game_id"],
                title=seed["title"],
                namespace=seed.get("namespace", "demo"),
                payload=seed["payload"],
            ))
        db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Mindfield Games — LLM Game Field Runtime")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup():
        init_db()
        load_all_genomes()
        seed_materials_if_empty()

    app.include_router(games.router)
    app.include_router(sessions.router)
    app.include_router(materials.router)
    app.include_router(llm_api.router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


app = create_app()
