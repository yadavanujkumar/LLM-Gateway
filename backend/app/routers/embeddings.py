import time
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.chat import EmbeddingRequest, EmbeddingResponse
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import limiter
from app.services.llm.router import route_embeddings
from app.services.usage import record_usage, record_log
from starlette.requests import Request

router = APIRouter(tags=["Embeddings"])


@router.post("/v1/embeddings")
@limiter.limit("60/minute")
async def create_embeddings(
    request: Request,
    body: EmbeddingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create embeddings for the provided input text."""
    start_time = time.perf_counter()
    try:
        result = await route_embeddings(body)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding provider error: {str(e)}",
        )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    usage = result.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)

    record_usage(
        db,
        user_id=current_user.id,
        model=result.get("model", body.model),
        prompt_tokens=prompt_tokens,
        completion_tokens=0,
    )
    record_log(
        db,
        user_id=current_user.id,
        model=result.get("model", body.model),
        prompt=json.dumps({"input": body.input}),
        response=None,
        prompt_tokens=prompt_tokens,
        completion_tokens=0,
        status="success",
        latency_ms=latency_ms,
    )
    return result
