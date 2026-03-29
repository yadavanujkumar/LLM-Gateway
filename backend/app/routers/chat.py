import time
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from app.middleware.auth import get_current_user
from app.middleware.rate_limit import limiter
from app.services.llm.router import route_chat_completion, route_chat_stream
from app.services.usage import record_usage, record_log
from app.services.cache import make_cache_key, get_cached_response, set_cached_response
from starlette.requests import Request

router = APIRouter(tags=["Chat"])


@router.post("/v1/chat/completions")
@limiter.limit("60/minute")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a chat completion. Compatible with OpenAI API format.
    Supports streaming via `stream: true`.
    """
    if body.stream:
        return StreamingResponse(
            _stream_response(body, current_user, db),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # Check cache for non-streaming requests
    messages_dict = [{"role": m.role.value, "content": m.content} for m in body.messages]
    cache_key = make_cache_key(body.model, messages_dict, temperature=body.temperature)
    cached = await get_cached_response(cache_key)
    if cached:
        # Still record usage from cache hit
        usage = cached.get("usage", {})
        record_usage(
            db,
            user_id=current_user.id,
            model=body.model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )
        cached["cached"] = True
        return cached

    start_time = time.perf_counter()
    try:
        result = await route_chat_completion(body)
    except Exception as e:
        record_log(
            db,
            user_id=current_user.id,
            model=body.model,
            prompt=json.dumps(messages_dict),
            response=None,
            prompt_tokens=0,
            completion_tokens=0,
            status="error",
            latency_ms=int((time.perf_counter() - start_time) * 1000),
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"LLM provider error: {str(e)}")

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    usage = result.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    # Record usage and log
    record_usage(
        db,
        user_id=current_user.id,
        model=result.get("model", body.model),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    record_log(
        db,
        user_id=current_user.id,
        model=result.get("model", body.model),
        prompt=json.dumps(messages_dict),
        response=result["choices"][0]["message"]["content"] if result.get("choices") else None,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        status="success",
        latency_ms=latency_ms,
    )

    # Cache the response (only for deterministic requests)
    if body.temperature == 0 or body.temperature is None:
        await set_cached_response(cache_key, result)

    return result


async def _stream_response(body: ChatCompletionRequest, user: User, db: Session):
    """Generator for streaming responses."""
    try:
        async for chunk in route_chat_stream(body):
            yield chunk
    except Exception as e:
        error_chunk = json.dumps({
            "error": {"message": str(e), "type": "stream_error"}
        })
        yield f"data: {error_chunk}\n\n"
        yield "data: [DONE]\n\n"
