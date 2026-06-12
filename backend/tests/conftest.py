import os
import sys
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("MINDFIELD_DB", str(db_file))
    monkeypatch.setenv("MINDFIELD_LLM", "mock")
    # Clear genome cache (lru) and reimport database with new env
    for mod in list(sys.modules):
        if mod.startswith("app"):
            del sys.modules[mod]
    from fastapi.testclient import TestClient
    from app.main import create_app
    app = create_app()
    with TestClient(app) as c:
        yield c
