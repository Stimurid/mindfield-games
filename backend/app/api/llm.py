from fastapi import APIRouter
from ..llm.provider import MODEL_PRESETS, get_provider

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/models")
def list_models():
    provider = get_provider()
    return {
        "presets": MODEL_PRESETS,
        "default": provider.default_model,
        "provider": type(provider).__name__,
    }
