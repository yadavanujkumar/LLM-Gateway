from datetime import datetime, timedelta
from typing import Optional, Dict
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.usage import Usage
from app.models.log import RequestLog
from app.config import settings


# Cost per 1K tokens per model (USD)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "text-embedding-ada-002": {"input": 0.0001, "output": 0.0},
    "mistral-small": {"input": 0.002, "output": 0.006},
    "mistral-medium": {"input": 0.0027, "output": 0.0081},
    "mistral-large": {"input": 0.008, "output": 0.024},
    "llama-3-8b": {"input": 0.0002, "output": 0.0002},
    "llama-3-70b": {"input": 0.0009, "output": 0.0009},
    "llama-3.1-8b-instruct": {"input": 0.0002, "output": 0.0002},
    "llama-3.1-70b-instruct": {"input": 0.0009, "output": 0.0009},
}

DEFAULT_PRICING = {"input": settings.STRIPE_PRICE_PER_1K_TOKENS, "output": settings.STRIPE_PRICE_PER_1K_TOKENS}


def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    cost = (prompt_tokens / 1000 * pricing["input"]) + \
           (completion_tokens / 1000 * pricing["output"])
    return round(cost, 8)


def record_usage(
    db: Session,
    user_id: uuid.UUID,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> Usage:
    total_tokens = prompt_tokens + completion_tokens
    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    usage = Usage(
        user_id=user_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost=cost,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def get_usage_summary(
    db: Session,
    user_id: uuid.UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict:
    query = db.query(Usage).filter(Usage.user_id == user_id)
    if start_date:
        query = query.filter(Usage.timestamp >= start_date)
    if end_date:
        query = query.filter(Usage.timestamp <= end_date)

    result = query.with_entities(
        func.count(Usage.id).label("total_requests"),
        func.sum(Usage.total_tokens).label("total_tokens"),
        func.sum(Usage.cost).label("total_cost"),
        func.sum(Usage.prompt_tokens).label("prompt_tokens"),
        func.sum(Usage.completion_tokens).label("completion_tokens"),
    ).first()

    return {
        "total_requests": result.total_requests or 0,
        "total_tokens": result.total_tokens or 0,
        "total_cost": round(result.total_cost or 0.0, 6),
        "prompt_tokens": result.prompt_tokens or 0,
        "completion_tokens": result.completion_tokens or 0,
    }


def record_log(
    db: Session,
    user_id: uuid.UUID,
    model: str,
    prompt: str,
    response: Optional[str],
    prompt_tokens: int,
    completion_tokens: int,
    status: str = "success",
    latency_ms: int = 0,
) -> RequestLog:
    log = RequestLog(
        user_id=user_id,
        model=model,
        prompt=prompt,
        response=response,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        status=status,
        latency_ms=latency_ms,
    )
    db.add(log)
    db.commit()
    return log
