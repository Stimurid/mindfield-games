from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import init_db, SessionLocal
from .models import Material
from .services.genome_loader import load_seed_materials, load_all_genomes
from .api import games, sessions, materials, llm as llm_api, operator, library, configurator, triage, admin, research


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
        from .services.migrations import run_migrations
        applied = run_migrations()
        if applied:
            print(f"[migrations] applied: {applied}")
        load_all_genomes()
        seed_materials_if_empty()
        from .services.corpus_ingest import ingest_corpus_if_needed
        result = ingest_corpus_if_needed()
        if result.get("ingested"):
            print(f"[corpus] ingested {result['ingested']} entries (total {result.get('total')})")
        from .services.organ_seed import seed_organs_if_empty
        org_result = seed_organs_if_empty()
        if org_result.get("added"):
            print(f"[organs] seeded {org_result['added']} canonical organs (total {org_result.get('total')})")
        from .services.maturity import backfill_default_maturity
        mat_result = backfill_default_maturity()
        if mat_result.get("applied"):
            print(f"[maturity] backfilled {mat_result['applied']} corpus entries")

    app.include_router(games.router)
    app.include_router(sessions.router)
    app.include_router(materials.router)
    app.include_router(llm_api.router)
    app.include_router(operator.router)
    app.include_router(library.router)
    app.include_router(configurator.router)
    app.include_router(triage.router)
    app.include_router(admin.router)
    app.include_router(research.router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


app = create_app()
