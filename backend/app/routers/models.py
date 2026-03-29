from fastapi import APIRouter

from app.services.llm.router import get_all_models

router = APIRouter(tags=["Models"])


@router.get("/v1/models")
async def list_models():
    """List all available LLM models."""
    models = get_all_models()
    return {"object": "list", "data": models}
