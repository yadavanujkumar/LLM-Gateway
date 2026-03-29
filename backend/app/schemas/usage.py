from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


class UsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    prompt_tokens: int
    completion_tokens: int


class UsageRecord(BaseModel):
    id: uuid.UUID
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class UsageResponse(BaseModel):
    summary: UsageSummary
    records: List[UsageRecord]
    page: int
    page_size: int
    total: int


class LogRecord(BaseModel):
    id: uuid.UUID
    model: str
    prompt: str
    response: Optional[str]
    total_tokens: int
    status: str
    latency_ms: int
    timestamp: datetime

    model_config = {"from_attributes": True}
